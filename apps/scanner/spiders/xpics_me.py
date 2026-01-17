import scrapy
import urllib.parse
import json
import jmespath


class XpicsMeSpider(scrapy.Spider):
    name = "xpics.me"
    emails = ["help@xpics.me", "abuse@global-layer.com"]

    def __init__(self, name_query=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not name_query:
            raise ValueError(
                "Please provide a name_query argument, e.g. -a name_query='Ariana Grande'"
            )
        self.name_query = name_query
        self.current_page = 0
        self.last_page_hash = None

    def start_requests(self):
        encoded_query = urllib.parse.quote(self.name_query)
        url = (
            f"https://www.xpics.me/api/v1/search?"
            f"q={encoded_query}&"
            f"page={self.current_page}&"
            f"types[]=image&types[]=video&types[]=gallery&nsfw[]=0"
        )
        yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        data = json.loads(response.text)
        posts = jmespath.search("data.posts", data) or []

        for post in posts:
            content_type = jmespath.search("content.type", post)

            # IMAGE
            if content_type == "image":
                img_url = jmespath.search("data.url", post)
                yield {"image": img_url, "video": []}

            # VIDEO
            elif content_type == "video":
                video_url = jmespath.search("data.videos_v2[0].url", post)
                thumbnails = jmespath.search("data.thumbnails", post)
                yield {
                    "video": video_url,
                    "image": thumbnails,
                }

        # Pagination — STOP if no next page
        next_page = jmespath.search("meta.nextPage", data)

        if next_page:
            yield scrapy.Request(url=next_page, callback=self.parse)
