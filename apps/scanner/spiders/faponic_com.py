import scrapy
import re

class FaponicComSpider(scrapy.Spider):
    name = "faponic.com"
    emails = ["faponic@gmail.com"]

    def __init__(self, name_query=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not name_query:
            raise ValueError(
                "Usage: scrapy crawl fapomic_dot_com -a name_query='Demi Lovato'"
            )

        self.name_query = name_query
        self.slug = self._slugify(self.name_query)

    def _slugify(self, text):
        """Convert text to lowercase, replace non-alphanumeric with '-', and strip '-'"""
        return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

    def start_requests(self):
        search_url = f"https://faponic.com/search/{self.slug}/"
        yield scrapy.Request(search_url, callback=self.parse)

    def parse(self, response):
        all_tags = response.xpath('//div[@class="author-content"]/a')
        for tag in all_tags:
            _title = tag.xpath("./text()").get()
            model_url = tag.xpath("./@href").get()

            title = self._slugify(_title) if _title else ""
            if self.slug in title:
                yield scrapy.Request(model_url, callback=self.parse_model)

    def parse_model(self, response):
        images = response.xpath('//div[@id="content"]//img/@src').getall()
        yield {"image": images}

        next_page = response.xpath('//div[@id="next_page"]/a/@href').get()
        if next_page:
            yield scrapy.Request(next_page, callback=self.parse_model)
