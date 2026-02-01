import scrapy
import re
import json
import urllib.parse
import jmespath

class NsfwXxxSpider(scrapy.Spider):
    name = "nsfw.xxx"
    emails = ["abuse@nsfw.xxx", "abuse@global-layer.com"]

    def __init__(self, name_query=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not name_query:
            raise ValueError(
                "Usage: scrapy crawl nsfw_dot_xxx -a name_query='Mia Khalifa'"
            )

        self.name_query = name_query
        self.slug = self._slugify(self.name_query)
        self.encoded_query = urllib.parse.quote(self.name_query).lower()

    def _slugify(self, text):
        return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

    def start_requests(self):
        api_url = f"https://nsfw.xxx/api/v1/search?q={self.encoded_query}&page=1&types[]=image&types[]=video&types[]=gallery&nsfw[]=0"
        yield scrapy.Request(api_url, callback=self.parse)

    def parse(self, response):
        try:
            js_data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.error("Failed to decode JSON")
            return

        post_data = jmespath.search("data.posts", js_data) or []

        for post in post_data:
            content = post.get("content") or {}
            _title = content.get("title")
            if not _title:
                continue

            title = self._slugify(_title)
            if self.slug not in title:
                continue

            _type = content.get("type")
            page_id = content.get("id")
            page_url = f"https://nsfw.xxx/post/{page_id}"
            post_info = post.get("data") or {}

            if _type == "image":
                image_url = post_info.get("url")
                if image_url:
                    
                    yield {
                        "page_url": page_url,
                        "image": image_url
                    }

            elif _type == "video":
                image_urls = post_info.get("url")
                video_url = post_info.get("videos", {}).get("mp4")
                yield {
                    "page_url": page_url,
                    "image": image_urls,
                    "video": video_url
                }

        next_page = js_data.get("meta", {}).get("nextPage")
        if next_page:
            yield scrapy.Request(next_page, callback=self.parse)
