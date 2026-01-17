import scrapy
import re


class PicazorComSpider(scrapy.Spider):
    name = "picazor.com"
    emails = ["dmca@picazor.com", "alexx.person@gmail.com"]

    def __init__(self, name_query=None, *args, **kwargs):
        super(PicazorComSpider, self).__init__(*args, **kwargs)
        if not name_query:
            raise ValueError(
                "Please provide a name_query argument, e.g. -a name_query='Ariana Grande' "
                "or multiple: -a name_query='Ariana Grande, Selena Gomez'"
            )
        self.name_query = name_query

        # Handle multiple names (comma-separated or list-like)
        if isinstance(name_query, str):
            # Split by comma and clean up spaces
            names = [
                n.strip().lower().replace(" ", "%20") for n in name_query.split(",")
            ]
        elif isinstance(name_query, (list, tuple)):
            names = [str(n).strip().lower().replace(" ", "%20") for n in name_query]
        else:
            raise ValueError("name_query must be a string or list")

        self.name_queries = names

    def clean(self, text):
        # lowercase + keep only letters & numbers
        return re.sub(r"[^a-z0-9]+", "", text.lower())

    def start_requests(self):
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0"
            )
        }

        for name in self.name_queries:
            url = f"https://picazor.com/ru/search/{name}"
            yield scrapy.Request(
                url=url,
                headers=headers,
                callback=self.parse,
                meta={"name_query": name},
            )

    def parse(self, response):
        profile_url = response.xpath(
            './/div[@class="block w-full"]/parent::a/@href'
        ).getall()
        for url in profile_url:
            yield scrapy.Request(
                url=response.urljoin(url),
                headers=response.request.headers,
                callback=self.parse_profile,
                meta={"name_query": self.name_query},
            )

    def parse_profile(self, response):
        # print("Profile URL:", response.url)

        # page = response.meta["page"]
        name_query = response.meta["name_query"]

        profile_text = response.xpath(".//h1/text()").get()
        tegs = response.xpath(".//h1/following-sibling::p/text()").getall()
        tegs = " ".join(tegs).strip()

        if self.clean(name_query) in self.clean(profile_text) or self.clean(
            name_query
        ) in self.clean(tegs):
            api_name = profile_text.strip().lower().replace(" ", "-")
            url = f"https://picazor.com/api/files/{api_name}/sfiles?page=1"
            yield scrapy.Request(
                url=url,
                headers=response.request.headers,
                callback=self.parse_files,
                meta={"page": 1, "name_query": api_name},
            )

    def parse_files(self, response):
        page = response.meta["page"]
        name_query = response.meta["name_query"]
        try:
            data = response.json()
        except Exception as e:
            self.logger.warning(f"Failed to parse JSON for {response.url}: {e}")
            return

        if not data:
            self.logger.info(f"No data for {name_query} page {page}")
            return

        for item in data:
            media_type = item.get("mime")
            media_url = item.get("path")

            if media_type == "photo":  # image
                yield {
                    "name": name_query,
                    "image": response.urljoin(media_url),
                    "video": [],
                }
            elif media_type == "video":  # video
                yield {
                    "name": name_query,
                    "image": [],
                    "video": response.urljoin(media_url),
                }

        # Next page
        next_page = page + 1
        next_url = f"https://picazor.com/api/files/{name_query}/sfiles?page={next_page}"

        yield scrapy.Request(
            url=next_url,
            headers=response.request.headers,
            callback=self.parse_files,
            meta={"page": next_page, "name_query": name_query},
            dont_filter=True,
        )
