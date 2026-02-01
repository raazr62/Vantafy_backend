import scrapy
import urllib.parse
import re

class Erothots1ComSpider(scrapy.Spider):
    name = "erothots1.com"
    emails = ["erothots@proton.me", "abuse@datacamp.co.uk"]

    custom_settings = {
        "CONCURRENT_REQUESTS": 1,
        # "TELNETCONSOLE_ENABLED": False
    }

    def __init__(self, name_query=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not name_query:
            raise ValueError(
                "Usage: scrapy crawl erothots1_dot_com -a name_query='caylinlive-10'"
            )

        self.name_query = name_query
        self.slug = self._slugify(self.name_query)
        self.encoded_query = urllib.parse.quote_plus(name_query).lower()
        # self.headers = {
        #     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        #     "Accept-Language": "en-GB,en;q=0.9",
        #     "Connection": "keep-alive",
        #     "Upgrade-Insecure-Requests": "1",
        #     "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        #     "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
        #     "sec-ch-ua-mobile": "?0",
        #     "sec-ch-ua-platform": '"macOS"',
        #     "Sec-Fetch-Dest": "document",
        #     "Sec-Fetch-Mode": "navigate",
        #     "Sec-Fetch-Site": "same-origin",
        #     "Sec-Fetch-User": "?1",
        # }

    def _slugify(self, text):
        return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

    def start_requests(self):
        format_list = ["videos", "photos"]
        for _type in format_list:
            # search_url = f"https://erothots1.com/{_type}/{self.encoded_query}"
            search_url = (
                f"https://erothots1.com/search/?q={self.encoded_query}&type={_type}"
            )
            yield scrapy.Request(search_url, callback=self.parse)

    def parse(self, response):
        # from scrapy.shell import inspect_response
        # inspect_response(response, self)
        if "/videos/" in response.url:
            video_tags = response.xpath('//a[@class="video video-media"]')
            for video_tag in video_tags:
                video_title = video_tag.xpath("./h3/text()").get()
                video_href = video_tag.xpath("./@href").get()

                _video_title = self._slugify(video_title) if video_title else ""

                if self.slug in _video_title:
                    yield scrapy.Request(video_href, callback=self.parse_video)

        elif "/photos/" in response.url:
            photo_tags = response.xpath('//a[@class="image-thumb"]')
            for photo_tag in photo_tags:
                photo_title = photo_tag.xpath("./h3/text()").get()
                photo_href = photo_tag.xpath("./@href").get()

                _photo_title = self._slugify(photo_title) if photo_title else ""

                if self.slug in _photo_title:
                    yield scrapy.Request(photo_href, callback=self.parse_photo)

        load_next = response.xpath('//a[@id="loadmore"]/@href').get()
        if load_next:
            yield scrapy.Request(load_next, callback=self.parse)

    def parse_video(self, response):
        # from scrapy.shell import inspect_response
        # inspect_response(response, self)
        video_url = response.xpath('//video[@class="v-player"]/source/@src').get()
        thumbnail = response.xpath('//meta[@property="og:image"]/@content').get()

        yield {
            "page_url": response.url,
            "video": video_url,
            "image": thumbnail
        }

    def parse_photo(self, response):
        img_url = response.xpath('//div[@class="item-picture mb-3"]/a/@data-src').get()
        if not img_url:
            return
        if ".webp" in img_url:
            image_url = response.xpath('//meta[@property="og:url"]/@content').get()
        else:
            image_url = img_url

        yield {
            "page_url": response.url,
            "image": image_url
        }