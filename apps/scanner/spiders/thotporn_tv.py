import scrapy
import json
import urllib.parse
import re


class ThotpornTvSpider(scrapy.Spider):
    name = "thotporn.tv"
    emails = [
        "abuse@alexhost.com",
        "f895bd8594c740248691900e450660e7.protect@withheldforprivacy.com",
        "abuse-alexhost@rnc.ro"
    ]
    def __init__(self, name_query=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not name_query:
            raise ValueError("Usage: scrapy crawl thotporn -a name_query='caylin'")

        self.name_query = name_query
        self.slug = self._slugify(self.name_query)
        self.encoded_query = urllib.parse.quote(name_query)

        self.headers = {
            "accept": "*/*",
            "accept-language": "en-GB,en;q=0.9",
            "x-requested-with": "XMLHttpRequest",
            "referer": "https://thotporn.tv/",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        }

    def _slugify(self, text):
        return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

    def start_requests(self):
        search_url = f"https://thotporn.tv/search?search={self.encoded_query}"
        yield scrapy.Request(search_url, headers=self.headers, callback=self.parse)

    def parse(self, response):
        js_data = json.loads(response.text)

        data_list = js_data.get("models", {}).get("data", [])
        if data_list:
            key = data_list[0].get("key")
            name = self._slugify(data_list[0].get("name"))

        if self.slug in name or self.slug in key:
            model_url = f"https://thotporn.tv/{key}?page=1&type=all&order=0"

            yield scrapy.Request(
                model_url,
                headers=self.headers,
                meta={"key": key},
                callback=self.profile_page,
            )

    def profile_page(self, response):
        key = response.meta.get("key")
        page = response.meta.get("page", 1)
        js_data = json.loads(response.text)

        if not js_data:
            return

        for data in js_data:
            g_id = data.get("get_id")
            _type = data.get("type")
            player = data.get("player")
            thumbnail = data.get("thumbnail")
            image_list = []

            if _type == 0:
                image_list.append(player)
                image_list.append(thumbnail)
                yield {
                    "video": [],
                    "image": image_list
                }

            elif _type == 1:
                yield {
                    "video": f"https://thotporn.tv/{key}/video/{g_id}",
                    "image": thumbnail,
                }

        next_page = page + 1
        next_url = f"https://thotporn.tv/{key}?page={next_page}&type=all&order=0"
        yield scrapy.Request(
            next_url,
            headers=self.headers,
            meta={"key": key, "page": next_page},
            callback=self.profile_page,
        )
