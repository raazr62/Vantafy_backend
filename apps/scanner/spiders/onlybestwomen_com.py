import scrapy
import re
import urllib.parse

class OnlybestwomenComSpider(scrapy.Spider):
    name = "onlybestwomen.com"
    emails = ["noc@alexhost.com", "special@onlybestwomen.com"]
    handle_httpstatus_list = [302]

    custom_settings = {
        "REDIRECT_ENABLED": False,
        #  "CONCURRENT_REQUESTS": 1,
    }

    def __init__(self, name_query=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not name_query:
            raise ValueError(
                "Usage: scrapy crawl cliptrend_dot_com -a name_query='Natasha Nice'"
            )

        self.name_query = name_query
        self.slug = self._slugify(self.name_query)
        self.encoded_query = urllib.parse.quote_plus(self.name_query)

    def _slugify(self, text):
        return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

    def start_requests(self):
        search_url = (
            f"https://www.onlybestwomen.com/advanced-results/?q={self.encoded_query}"
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
                    '//div[@class="nova-grid-cell nova-grid-thumb"]//a/img/@itemprop'
                ).getall()
                yield {"image": images}

        next_page = response.xpath('//a[@class="nova-next button-text"]/@href').get()
        if next_page:
            yield scrapy.Request(
                url=response.urljoin(next_page), callback=self.parse_model
            )
