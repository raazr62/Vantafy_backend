import scrapy
import json
import re
class LeakedzoneComSpider(scrapy.Spider):
    name = "leakedzone.com"
    emails = [
        "abuse@alexhost.com",
        "f895bd8594c740248691900e450660e7.protect@withheldforprivacy.com",
        "abuse-alexhost@rnc.ro",
    ]
    custom_settings = {
        "CONCURRENT_REQUESTS": 500,
    }

    def __init__(self, name_query=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not name_query:
            raise ValueError("Usage: scrapy crawl leaked -a name_query='caylin'")

        self.name_query = name_query
        self.slug = self._slugify(self.name_query)
        self.headers = {
            "accept": "*/*",
            "accept-language": "en-GB,en;q=0.9",
            "x-requested-with": "XMLHttpRequest",
            "referer": "https://leakedzone.com/",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        }

    def _slugify(self, text):
        return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

    def start_requests(self):
        url = "https://leakedzone.com/creators"
        yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        all_creator = response.xpath('//article[@class="movie-item"]/a')
        for creator in all_creator:
            creator_name = creator.xpath('.//h3[@class="movie-link"]/text()').get()
            key = (creator.xpath('.//span[@class="date"]/text()').get()).lstrip("@")

            if self.slug in self._slugify(creator_name):
                model_url = f"https://leakedzone.com/{key}?page=1&type=all&order=0"
                yield scrapy.Request(
                    model_url,
                    headers=self.headers,
                    meta={"key": key},
                    callback=self.profile_page,
                )

        total_page = int(
            response.xpath('//li[@class="page-item hidden-xs"]/a/text()').get()
        )
        for page in range(2, total_page + 1):
            page_url = f"https://leakedzone.com/creators?page={page}"
            yield scrapy.Request(page_url, callback=self.parse)

    def profile_page(self, response):
        key = response.meta.get("key")
        page = response.meta.get("page", 1)
        js_data = json.loads(response.text)

        if not js_data:
            return

        for data in js_data:
            item = {}
            g_id = data.get("get_id")
            _type = data.get("type")
            _image = data.get("image")
            thumbnail = data.get("thumbnail")

            if _type == 0:
                item["page_url"] = f"https://leakedzone.com/{key}/photo/{g_id}"
                item["image"] = f"https://leakedzone.com/storage/{_image}"

            elif _type == 1:
                item["page_url"] = f"https://leakedzone.com/{key}/video/{g_id}"
                item["image"] = thumbnail

            yield item

        next_page = page + 1
        next_url = f"https://leakedzone.com/{key}?page={next_page}&type=all&order=0"
        yield scrapy.Request(
            next_url,
            headers=self.headers,
            meta={"key": key, "page": next_page},
            callback=self.profile_page,
        )
