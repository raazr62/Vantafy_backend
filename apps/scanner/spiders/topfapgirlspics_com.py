import scrapy
import urllib.parse
import random
import re

class TopfapgirlspicsComSpider(scrapy.Spider):
    name = "topfapgirlspics.com"
    emails = ["piava@topfapgirlspics.com", "noc@alexhost.com"]
    handle_httpstatus_list = [302]

    custom_settings = {
        "REDIRECT_ENABLED": False,
        "COOKIES_ENABLED": True,
        "CONCURRENT_REQUESTS": 1,
        "DOWNLOAD_DELAY": 1,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
    }

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0",
    ]

    ACCEPT_LANG = ["en-US,en;q=0.9", "en-GB,en;q=0.8", "en;q=0.7"]

    def random_headers(self, referer=None):
        """Generate fresh headers every request"""
        return {
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept-Language": random.choice(self.ACCEPT_LANG),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": referer or "https://www.topfapgirlspics.com/",
            "Upgrade-Insecure-Requests": "1",
        }

    def __init__(self, name_query=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not name_query:
            raise ValueError(
                "Usage: scrapy crawl topfapgirlspics_dot_com -a name_query='Mia Khalifa'"
            )

        self.name_query = name_query
        self.slug = self._slugify(name_query)
        self.encoded_query = urllib.parse.quote_plus(name_query)

    def _slugify(self, text):
        return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

    def start_requests(self):
        url = f"https://www.topfapgirlspics.com/search/?q={self.encoded_query}"

        yield scrapy.Request(
            url,
            headers=self.random_headers(),
            callback=self.parse_search,
            meta={"dont_redirect": True},
        )

    def parse_search(self, response):
        redirect = response.headers.get("Location")
        if not redirect:
            self.logger.warning("No redirect found!")
            return

        final = response.urljoin(redirect.decode())

        yield scrapy.Request(
            final,
            headers=self.random_headers(referer=response.url),
            callback=self.parse_model,
        )

    def parse_model(self, response):
        if response.status == 302:
            self.logger.warning(f"[302 BLOCKED] Retrying: {response.url}")
            yield scrapy.Request(
                response.url,
                headers=self.random_headers(referer=response.url),
                callback=self.parse_model,
                dont_filter=True,
            )
            return

        name = response.xpath('//h1[@itemprop="name"]/text()').get()
        if name:
            slug = self._slugify(name)
            if self.slug in slug:
                data = response.xpath(
                    '//div[@class="grid_item thumb"]//a'
                )
                for i in data:
                    image = i.xpath(".//img/@itemprop").get()
                    page_url = i.xpath(".//@href").get()

                    yield {
                        "page_url": response.urljoin(page_url),
                        "images": image
                    }

        next_page = response.xpath('//a[@class="next button-text"]/@href').get()
        if next_page:
            yield scrapy.Request(
                response.urljoin(next_page),
                headers=self.random_headers(referer=response.url),
                callback=self.parse_model,
                dont_filter=True,
            )
