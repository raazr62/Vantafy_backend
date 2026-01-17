import scrapy
import re

class NudostarTvSpider(scrapy.Spider):
    name = "nudostar.tv"
    emails = [
        "johnnysinsmom@gmail.com",
        "OWNER@fapopedia.net.customers.whoisprivacycorp.com",
    ]

    def __init__(self, name_query=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not name_query:
            raise ValueError(
                "Usage: scrapy crawl nudostar_dot_tv -a name_query='Mia Khalifa'"
            )

        self.name_query = name_query
        self.slug = self._slugify(self.name_query)

    def _slugify(self, text):
        """Convert text to lowercase, replace non-alphanumeric with '-', and strip '-'"""
        return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

    def start_requests(self):
        search_url = f"https://nudostar.tv/models/{self.slug}/"
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-IN,en-US;q=0.9,en;q=0.8,gu;q=0.7",
            "cache-control": "max-age=0",
            "dnt": "1",
            "priority": "u=0, i",
            "referer": "https://nudostar.tv/",
            "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
            "Cookie": "kt_tcookie=1; __PPU_puid=7552005876070514742; _ga=GA1.1.891209443.1764216097; __PPU_ppucnt=2; _ga_MHZ35ECCSX=GS2.1.s1764216096$o1$g1$t1764216649$j7$l0$h0; __PPU_cl_tl=IIKhbNJpI9ywoWMBAYKhbNJpHGfnoWMVzRAAgqFs0mkcZ-ehYxnNAgCCoWzSaRb4_aFjA8yAgqFs0mjOG_2hYwPOAAIAAIKhbNJpGATQoWMCzgABAACCoWzSaRxn56FjFQ; UGVyc2lzdFN0b3JhZ2U=%7B%22CAIFRQ%22%3A%22ADhuTwAAAAAAAAAJADhJKgAAAAAAAAADADaV2wAAAAAAAAAGACwWkQAAAAAAAAADACcGsQAAAAAAAAADACcFKwAAAAAAAAADACcFKgAAAAAAAAAD%22%2C%22CAIFRT%22%3A%22ADhuTwAAAABpKSxQADhJKgAAAABpKSxQADaV2wAAAABpKSxQACwWkQAAAABpJ9rQACcGsQAAAABpJ9rQACcFKwAAAABpJ9rQACcFKgAAAABpJ9rQ%22%2C%22MTIFRQ%22%3A%22AEs66QAAAAAAAAADAEs65wAAAAAAAAAGAEsQuQAAAAAAAAADAElBxgAAAAAAAAADAElBxQAAAAAAAAAD%22%2C%22MTIFRT%22%3A%22AEs66QAAAABpKSxQAEs65wAAAABpKSxQAEsQuQAAAABpKSxQAElBxgAAAABpKSxQAElBxQAAAABpKSxQ%22%7D; bnState_2053292=%7B%22impressions%22%3A30%2C%22delayStarted%22%3A0%7D",
        }

        yield scrapy.Request(search_url, headers=headers, callback=self.parse)

    def parse(self, response):
        _title = response.xpath("//h1/text()").get()
        if _title:
            title = self._slugify(_title)
            if self.slug in title:
                all_images = response.xpath(
                    '//div[@id="list_videos_common_videos_list_items"]//img/@src'
                ).getall()
                images = [re.sub(r"_\d+px(?=\.\w+$)", "", _img) for _img in all_images]
                yield {"image": images}

        next_page = response.xpath('//a[text()="Next"]/@href').get()
        if next_page:
            yield scrapy.Request(next_page, callback=self.parse)
