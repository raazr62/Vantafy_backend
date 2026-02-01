import scrapy
import urllib.parse
import re


class EromeFanSpider(scrapy.Spider):
    name = "erome.fan"
    emails = ["contact@erome.fan"]
    custom_settings = {
        "DOWNLOAD_DELAY": 1,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "CONCURRENT_REQUESTS": 2,
        "RETRY_TIMES": 1,
        "DOWNLOAD_TIMEOUT": 20,
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0",
    }

    def __init__(self, name_query=None, *args, **kwargs):
        super(EromeFanSpider, self).__init__(*args, **kwargs)
        if not name_query:
            raise ValueError(
                "Please provide a name_query argument, e.g.: -a name_query='Ariana Grande'"
            )
        self.creator = name_query
        self.name_query = name_query
        encoded_query = urllib.parse.quote(name_query)
        self.start_urls = [f"https://erome.fan/?s={encoded_query}"]

    def clean(self, text):
        return re.sub(r"[^a-z0-9]+", "", text.lower()).strip("-")

    def start_requests(self):
        headers = {
            "accept": "text/plain, */*; q=0.01",
            "accept-language": "en-US,en;q=0.9",
            "priority": "u=1, i",
            "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/141.0.0.0 Safari/537.36",
            "x-requested-with": "XMLHttpRequest",
        }
        yield scrapy.Request(
            url=self.start_urls[0], headers=headers, callback=self.parse
        )

    def parse(self, response):
        urls = response.xpath(
            './/main[@id="main"]//a[@class="album-link"]//@href'
        ).getall()
        for url in urls:
            yield scrapy.Request(url=response.urljoin(url), callback=self.parse_product)
        next_page = response.xpath('.//a[@class="next page-numbers"]/@href').get()
        if next_page:
            yield scrapy.Request(url=response.urljoin(next_page), callback=self.parse)

    def parse_product(self, response):
        title = response.xpath('.//h1[@itemprop="headline"]/text()').get()
        username = response.xpath('.//a[@id="user_name"]/text()').get()
        tags = response.xpath('.//p[@class="mt-10"]/text()').getall()
        # tags = " ".join(tags)

        if (
            self.clean(self.name_query) in self.clean(title)
            or self.clean(self.name_query) in self.clean(username)
            or any(self.clean(self.name_query) in self.clean(tag) for tag in tags)
        ):
            groups = response.xpath('.//div[contains(@class,"media-group")]')
            for i in groups:
                # For video posts
                if i.xpath('.//div[@class="video"]'):
                    image = i.xpath('.//div[@class="video"]//video/@src').get()
                    video = i.xpath('.//div[@class="video"]//video/source/@src').get()
                    yield {
                        "page_url": response.url,
                        "image": image,
                        "video": video
                    }
                # For image posts
                elif i.xpath('.//div[@class="img"]'):
                    image = i.xpath('.//div[@class="img"]/@data-src').get()
                    yield {
                        "page_url": response.url, 
                        "image": image
                    }
