import scrapy
import urllib.parse
import re

class LeaksphotosComSpider(scrapy.Spider):
    name = "leaksphotos.com"
    emails = ["assist@leaksphotos.com", "noc@alexhost.com"]
    handle_httpstatus_list = [302]

    custom_settings = {
        "REDIRECT_ENABLED": False,
        #  "CONCURRENT_REQUESTS": 1,
    }

    def __init__(self, name_query=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not name_query:
            raise ValueError(
                "Usage: scrapy crawl leaksphotos_dot_com -a name_query='Mia Khalifa'"
            )

        self.name_query = name_query
        self.slug = self._slugify(self.name_query)
        self.encoded_query = urllib.parse.quote_plus(self.name_query)

    def _slugify(self, text):
        return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

    def start_requests(self):
        search_url = (
            f"https://www.leaksphotos.com/search-models/?q={self.encoded_query}"
        )
        yield scrapy.Request(
            search_url,
            callback=self.parse,
            meta={"dont_redirect": True},
            dont_filter=True,
        )

    def parse(self, response):
        redirect = response.headers.get("Location")
        if redirect:
            redirect = redirect.decode()
            final_url = response.urljoin(redirect)

            yield scrapy.Request(final_url, callback=self.parse_model)
        else:
            print("No redirect!")

    def parse_model(self, response):
        name = response.xpath('//h1[@itemprop="name"]/text()').get()
        if name:
            _name = self._slugify(name)
            if self.slug in _name:
                images = response.xpath(
                    '//div[@class="grid-item thumb"]//span/img/@itemprop'
                ).getall()
                page_url = response.xpath(
                    '//div[@class="grid-item thumb"]//span/@ data-mtid'
                ).getall()
                yield {
                    "page_url": [
                        f"https://www.leaksphotos.com/image-gallery/?slug={i}"
                        for i in page_url
                    ],
                    "image": images,
                }

        next_page = response.xpath('//a[@class="pager-next button-text"]/@href').get()
        if next_page:
            yield scrapy.Request(
                url=response.urljoin(next_page), callback=self.parse_model
            )
