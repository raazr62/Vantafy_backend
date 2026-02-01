import scrapy
import urllib.parse
import json
import jmespath
import re

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
            title = jmespath.search("content.title",post)
            slug = jmespath.search("user.slug", post)
            tags = jmespath.search("categories[].slug",post)
            tags = " ".join(tags) if tags else ""

            # match if the self.name_query is match with title , slug or tags
            clean_name_query = self.clean(self.name_query)
            clean_title = self.clean(title) if title else ""
            clean_slug = self.clean(slug) if slug else ""
            clean_tags = self.clean(tags) if tags else ""
            if (clean_name_query not in clean_title and
                clean_name_query not in clean_slug and
                clean_name_query not in clean_tags):
                continue  # skip this post if no match

            content_type = jmespath.search("content.type", post)
            post_id = jmespath.search("content.id", post)

            page_url = f"https://www.xpics.me/@{slug}/{post_id}"

            # IMAGE
            if content_type == "image":
                img_url = jmespath.search("data.url", post)
                yield {
                    "page_url": page_url,
                    "image": img_url,
                }

            # VIDEO
            elif content_type == "video":
                video_url = jmespath.search("data.videos_v2[0].url", post)
                thumbnails = jmespath.search("data.thumbnails", post)
                yield {
                    "page_url": page_url,
                    "video": video_url,
                    "image": thumbnails,
                }

            elif content_type == "gallery":
                gallery_images = jmespath.search("data.urls",post)
                yield {
                    "page_url": page_url,
                    "image": gallery_images
                }

        # Pagination — STOP if no next page
        next_page = jmespath.search("meta.nextPage", data)

        if next_page:
            yield scrapy.Request(url=next_page, callback=self.parse)

    def clean(self, text):
        # lowercase + keep only letters & numbers
        return re.sub(r"[^a-z0-9]+", "", text.lower())
