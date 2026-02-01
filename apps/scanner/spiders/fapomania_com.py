import scrapy
import re

class FapomaniaComSpider(scrapy.Spider):
    name = "fapomania.com"
    emails = ["fapomania990@gmail.com", "abuse@serverel.com"]

    def __init__(self, name_query=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not name_query:
            raise ValueError(
                "Usage: scrapy crawl fapomania_dot_com -a name_query='Demi Lovato'"
            )

        self.name_query = name_query
        self.slug = self._slugify(self.name_query)
        self.first_letter = self.slug[0]

    def _slugify(self, text):
        return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

    def start_requests(self):
        url1 = f"https://fapomania.com/onlyfans/{self.first_letter}/"
        yield scrapy.Request(url1, callback=self.parse_letter_page)

        url2 = f"https://fapomania.com/list/{self.first_letter}/"
        yield scrapy.Request(url2, callback=self.parse_list_page)

    def parse_letter_page(self, response):
        models = response.xpath('//div[@class="previzako"]/a')
        for m in models:
            model_name = m.xpath("./p/text()").get()
            model_url = m.xpath("./@href").get()
            if self.slug in self._slugify(model_name):
                yield response.follow(model_url, callback=self.parse_model_page)
                return

        next_page = response.xpath(
            '(//li[a[@class="active"]])[2]/following-sibling::li/a/@href'
        ).get()
        if next_page:
            yield response.follow(next_page, callback=self.parse_letter_page)

    def parse_list_page(self, response):
        models_list = response.xpath('(//div[@class="previzakosblo"])[1]//a')
        for _m in models_list:
            _model_url = _m.xpath("./@href").get()
            _model_name = _m.xpath(".//img/@alt").get()
            if self.slug in self._slugify(_model_name):
                yield response.follow(_model_url, callback=self.parse_model_page)
                return

    def parse_model_page(self, response):
        title_text = response.xpath('//div[@class="modlublaroimag"]/img/@alt').get()
        if not title_text:
            return

        if self._slugify(title_text) != self.slug:
            return

        post = response.xpath('//div[@class="leftocontar"]//div[@class="previzako"]')
        for i in post:
            page_url = i.xpath(".//a/@href").get()
            img = i.xpath(
                './/div[@class="previzakoimag"]/img/@src'
            ).get()

            if "_300px" in img:
                img = re.sub(r"_300px(?=\.\w+$)", "", img)
                
                yield {
                    "page_url": page_url,
                    "image": img
                }

        next_page = response.xpath('//a[contains(text(), "Next")]/@href').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse_model_page)
