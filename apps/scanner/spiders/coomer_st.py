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
            video = None
            all_files = []

            if post.get("file"):
                all_files.append(post["file"])
            if post.get("attachments"):
                all_files.extend(post["attachments"])

            for f in all_files:
                path = f.get("path")
                if not path:
                    continue

                url = f"https://img.coomer.st/thumbnail/data{path}"

                if url.endswith((".m4v", ".mp4")) and not video:
                    video = (
                        f"https://coomer.st/onlyfans/user/{match_id}/post/{post['id']}"
                    )
                elif url.endswith(".jpg"):
                    images.append(url)

            yield {"image": images, "video": [video] if video else []}

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
