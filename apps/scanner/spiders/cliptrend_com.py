import scrapy
import re
import urllib.parse


class CliptrendComSpider(scrapy.Spider):
    name = "cliptrend.com"
    emails = ["thecliptrend@gmail.com", "admin@frantech.ca"]

    custom_settings = {"TELNETCONSOLE_ENABLED": False}

    def __init__(self, name_query=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not name_query:
            raise ValueError(
                "Usage: scrapy crawl cliptrend_dot_com -a name_query='Natasha Nice'"
            )

        self.name_query = name_query
        self.slug = self._slugify(self.name_query)
        self.encoded_query = urllib.parse.quote_plus(self.name_query).lower()

        self.headers = {
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
            "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
        }

    def _slugify(self, text):
        return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

    def start_requests(self):
        search_url = f"https://cliptrend.com/?s={self.encoded_query}"
        yield scrapy.Request(search_url, headers=self.headers, callback=self.parse)

    def parse(self, response):
        video_tags = response.xpath("//h6/a")
        for tag in video_tags:
            title_head = tag.xpath(".//@title").get()
            video_url = tag.xpath(".//@href").get()

            if not title_head or not video_url:
                continue

            title = self._slugify(title_head)
            if self.slug in title:
                yield scrapy.Request(
                    video_url, headers=self.headers, callback=self.parse_details
                )

        next_page = response.xpath('//a[text()="NEXT"]/@href').get()
        if next_page:
            yield scrapy.Request(next_page, headers=self.headers, callback=self.parse)

    def parse_details(self, response):
        video_href = response.xpath('//meta[@property="og:url"]/@content').get()
        thumbnail = response.xpath('//meta[@itemprop="thumbnailUrl"]/@content').get()

        yield {"video": video_href, "image": thumbnail}
