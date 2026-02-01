import scrapy
import json
import re


class DankwankNetSpider(scrapy.Spider):
    name = "dankwank.net"
    emails = ["admin@frantech.ca"]

    def __init__(self, name_query=None, *args, **kwargs):
        super(DankwankNetSpider, self).__init__(*args, **kwargs)
        super().__init__(*args, **kwargs)

        if not name_query:
            raise ValueError(
                "Provide a name_query. Example: -a name_query='Angela White'"
            )
        self.name_query = name_query

        # Multiple names support
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
                "Chrome/142.0.0.0 Safari/537.36"
            )
        }

        for name in self.name_queries:
            url = f"https://dankwank.net/search/{name}/"
            yield scrapy.Request(
                url=url,
                headers=headers,
                callback=self.parse,
                meta={"page": 1, "name_query": name},
            )

    def parse(self, response):
        name = response.meta["name_query"]
        # name_title = response.url.split("/")[-2].replace("-", " ").lower()
        # print(name_title)

        # img = response.xpath(
        #     f".//img[contains(translate(@alt, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{name_title}')]/@src"
        # ).getall()
        # if img:
        #     yield {"image": img, "video": []}

        post_links = response.xpath(
            './/div[@class="item-col col -video"]/a/@href'
        ).getall()
        for post in post_links:
            yield scrapy.Request(
                url=response.urljoin(post),
                headers=response.request.headers,
                callback=self.parse_post,
                meta={"name_query": name},
            )

        next_page = response.xpath('.//a[@rel="next"]/@href').get()

        if next_page:
            yield scrapy.Request(
                url=response.urljoin(next_page),
                headers=response.request.headers,
                callback=self.parse,
                meta={"name_query": name},
            )

    def parse_post(self, response):
        name_query = response.meta.get("name_query")
        json_text = response.xpath(
            './/script[@type="application/ld+json"]/text()'
        ).get()

        # img = response.xpath('.//video[@class="video-js"]/@poster').get()

        if json_text:
            data = json.loads(json_text)
        else:
            data = {}
            self.logger.warning("JSON data not found")
        
        video_text = data.get("name", "")
        description = data.get("description", "")
        

        tag = response.xpath('.//div[@class="content-links -tags"]/a/text()').getall()
        tag = " ".join(tag)
        if (
            self.clean(name_query) in self.clean(video_text)
            or self.clean(name_query) in self.clean(tag)
            or self.clean(name_query) in self.clean(description)
        ):
            video = data.get("embedUrl")
            img = data.get("thumbnailUrl")

            yield {
                "page_url" : response.url,
                "image": img,
                "video": video
            }
