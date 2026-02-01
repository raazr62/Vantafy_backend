import scrapy
import re


class ThothdComSpider(scrapy.Spider):
    name = "thothd.com"
    emails = ["abuse@koddos.net"]

    def __init__(self, name_query=None, *args, **kwargs):
        super(ThothdComSpider, self).__init__(*args, **kwargs)
        if not name_query:
            raise ValueError(
                "Please provide a name_query argument, e.g. -a name_query='Ariana Grande'"
            )
        self.name_query = name_query

        if isinstance(name_query, str):
            names = [n.strip().lower().replace(" ", "-") for n in name_query.split(",")]
        elif isinstance(name_query, (list, tuple)):
            names = [str(n).strip().lower().replace(" ", "-") for n in name_query]
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
            for base_url in ["https://thothd.com"]:
                url = f"{base_url}/search/{name}/"
                yield scrapy.Request(
                    url=url,
                    headers=headers,
                    callback=self.parse,
                    meta={
                        "name": name,
                        "page": 1,
                        "headers": headers,
                        "base_url": base_url,
                    },
                )

    def parse(self, response):
        if response.status == 404:
            self.logger.warning(f"❌ Model not found: {response.url}")
            return None

        name = response.meta["name"]
        page = response.meta["page"]
        headers = response.meta["headers"]
        base_url = response.meta["base_url"]
        # xpath_name = name.replace("-", " ").lower()

        post_urls = response.xpath('.//div[@class="item  "]//@href').getall()

        for post_url in post_urls:
            yield {"image": [], "video": post_url}
            yield scrapy.Request(
                url=post_url,
                headers=headers,
                callback=self.parse_post,
                meta={"headers": headers, "name_query": name},
            )

        #     # Crawl next page
        next_page = page + 1
        next_url = f"{base_url}/search/{name}/?from_videos={next_page}"
        yield scrapy.Request(
            url=next_url,
            headers=headers,
            callback=self.parse,
            meta={
                "page": next_page,
                "headers": headers,
                "name": name,
                "base_url": base_url,
            },
        )

    def parse_post(self, response):
        name_query = response.meta.get("name_query")
        tegs = response.xpath(
            './/div[@class="item"][contains(text(),"Tags")]/a/text()'
        ).getall()
        video_text = response.xpath('.//div[@class="headline"]/h1/text()').get()

        tegs = " ".join(tegs)

        if self.clean(name_query) in self.clean(video_text) or self.clean(
            name_query
        ) in self.clean(tegs):

            img_url = response.xpath('.//a[@rel="screenshots"]/@href').getall()
            for url in img_url:
                yield {
                    "page_url": response.url,
                    "image": url
                }
