import scrapy
import re

class LeakedmodelsComSpider(scrapy.Spider):
    name = "leakedmodels.com"
    emails = ["leakedmodmca@gmail.com ", "abuse@serverel.com"]

    def __init__(self, name_query=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not name_query:
            raise ValueError(
                "Usage: scrapy crawl leakedmodels_dot_com -a name_query='Natasha Nice'"
            )

        self.name_query = name_query
        self.slug = self._slugify(self.name_query)

    def _slugify(self, text):
        return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

    def start_requests(self):
        search_url = f"https://leakedmodels.com/search/?s={self.slug}"
        yield scrapy.Request(search_url, callback=self.parse)

    def parse(self, response):
        tags = response.xpath('//h2[@class="entry-title heading-size-1"]/a')
        for tag in tags:
            title = tag.xpath("./text()").get()
            model_url = tag.xpath("./@href").get()

            _title = self._slugify(title) if title else ""

            if self.slug in _title:
                yield scrapy.Request(model_url, callback=self.parse_model)

    def parse_model(self, response):
        images = response.xpath('//div[@class="entry-content"]//img/@src').getall()
        page_url = response.xpath('//div[@class="entry-content"]/p/a/@href').getall()
        cleaned_images = [re.sub(r"_thb(?=\.\w+$)", "", img) for img in images]
        yield {
            "page_url":page_url,
            "image": cleaned_images
        }

        next_page = response.xpath('//a[@class="next page-numbers"]/@href').get()
        if next_page:
            yield scrapy.Request(next_page, callback=self.parse_model)
