import scrapy
import re
import json


class CoomerStSpider(scrapy.Spider):
    name = "coomer.st"
    handle_httpstatus_list = [400]
    emails = ["contact@coomer.email"]

    custom_settings = {"CONCURRENT_REQUESTS": 1, "TELNETCONSOLE_ENABLED": False}

    def __init__(self, name_query=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not name_query:
            raise ValueError(
                "Usage: scrapy crawl coomer_dot_st -a name_query='caylinlivefree'"
            )

        self.name_query = name_query
        self.slug = self._clean_query(self.name_query)

        self.headers = {
            "accept": "text/css",
        }

    def _clean_query(self, text):
        return re.sub(r"[^a-z0-9]+", "", text.lower())

    def start_requests(self):
        url = "https://coomer.st/api/v1/creators"
        yield scrapy.Request(url, headers=self.headers, callback=self.parse)

    def parse(self, response):
        try:
            js_data = json.loads(response.text)
        except:
            js_data = []

        for ids in js_data:
            match_id = ids.get("id", "")
            if self.slug in match_id:
                model_url = f"https://coomer.st/api/v1/onlyfans/user/{match_id}/posts"
                yield scrapy.Request(
                    model_url,
                    meta={"match_id": match_id, "offset": 0},
                    headers=self.headers,
                    callback=self.parse_posts,
                )

    def parse_posts(self, response):
        if response.status == 400:
            return

        match_id = response.meta["match_id"]
        offset = response.meta.get("offset", 0)

        posts = json.loads(response.text)
        if not posts:
            return

        for post in posts:
            images = []
            videos = []

            file = post.get("file").get("path")
            if file:
                file = response.urljoin(file)
                if file.endswith((".jpg", ".jpeg", ".png", ".gif")):
                    images.append(file)
                elif file.endswith((".mp4", ".m4v", ".wmv", ".avi", ".mkv")):
                    videos.append(file)

            attachments = post.get("attachments")
            for attatch in attachments:
                data = attatch.get("path")
                if data:
                    data = response.urljoin(data)
                    if data.endswith((".jpg", ".jpeg", ".png", ".gif")):
                        images.append(data)
                    elif data.endswith((".mp4", ".m4v", ".wmv", ".avi", ".mkv")):
                        videos.append(data)

            id = post.get("id")
            user = post.get("user")
            service = post.get("service")

            page_url = f"https://coomer.st/{service}/user/{user}/post/{id}"

            yield {
                "page_url": page_url,
                "image": images,
                "video": videos
            }

        next_offset = offset + 50
        next_url = (
            f"https://coomer.st/api/v1/onlyfans/user/{match_id}/posts?o={next_offset}"
        )
        yield scrapy.Request(
            next_url,
            meta={"match_id": match_id, "offset": next_offset},
            headers=self.headers,
            callback=self.parse_posts,
        )
