import scrapy
import re

class NudogramComSpider(scrapy.Spider):
    name = "nudogram.com"
    emails = ["nudogram@gmail.com", "abuse@serverel.com"]

    def __init__(self, name_query=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not name_query:
            raise ValueError(
                "Usage: scrapy crawl nudogram_dot_com -a name_query='Mia Khalifa'"
            )

        self.name_query = name_query
        self.slug = self._slugify(self.name_query)

    def _slugify(self, text):
        """Convert text to lowercase, replace non-alphanumeric with '-', and strip '-'"""
        return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

    def start_requests(self):
        search_url = f"https://nudogram.com/search/{self.slug}/"
        yield scrapy.Request(search_url, callback=self.parse)

    def parse(self, response):
        all_tags = response.xpath('//div[@class="item  "]/a')
        for tag in all_tags:
            _title = tag.xpath("./@title").get()
            model_url = tag.xpath("./@href").get()

            title = self._slugify(_title) if _title else ""
            if self.slug in title:
                yield scrapy.Request(model_url, callback=self.parse_model)

    def parse_model(self, response):
        images = response.xpath('//div[@class="item  "]//img/@src').getall()
        for _img in images:
            image_url = re.sub(r"_280(?=\.\w+$)", "", _img)
            yield {"image": image_url}

        next_page = response.xpath(
            '//li[@class="page"][span]//following-sibling::li/a/@href'
        ).get()
        if next_page:
            yield scrapy.Request(next_page, callback=self.parse_model)
