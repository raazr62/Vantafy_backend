import scrapy
import re


class FapezaComSpider(scrapy.Spider):
    name = "fapeza.com"
    emails = ["fapezan@gmail.com", "abuse@serverel.com"]
    custom_settings = {"CONCURRENT_REQUESTS": 1, "TELNETCONSOLE_ENABLED": False}

    def __init__(self, name_query=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not name_query:
            raise ValueError(
                "Usage: scrapy crawl fapeza_dot_com -a name_query='Fadinha Maju'"
            )

        self.name_query = name_query
        self.slug = self._slugify(self.name_query)

    def _slugify(self, text):
        return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

    def start_requests(self):
        search_url = f"https://fapeza.com/search/{self.slug}/"
        yield scrapy.Request(search_url, callback=self.parse)

    def parse(self, response):
        all_acc = response.xpath('.//div[@class="img-container"]/a/@href').getall()
        for ac_url in all_acc:
            if self.slug in ac_url:
                yield scrapy.Request(ac_url, callback=self.parse_account)

    def parse_account(self, response):
        all_images = response.xpath('//img[@class="thumb_img"]/@src').getall()
        for img in all_images:
            if img:
                image_url = re.sub(r"_400px(?=\.\w+$)", "", img)
                yield {"image": image_url}

        next_page = response.xpath('//div[@id="load_more"]/@data-page').get()
        max_page = response.xpath('//div[@id="load_more"]/@data-max').get()
        
        if next_page and int(next_page) <= int(max_page):
            next_url = response.xpath(
                '//div[@id="load_more"]//a[@class="load-more-button"]/@href'
            ).get()
            if next_url:
                yield response.follow(next_url, callback=self.parse_account)
