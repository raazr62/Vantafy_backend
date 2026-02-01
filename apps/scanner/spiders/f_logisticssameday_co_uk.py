import scrapy
import re

class FLogisticssamedayCoUkSpider(scrapy.Spider):
    name = "f.logisticssameday.co.uk"
    emails = ["abuse@eurohoster.org"]

    def __init__(self, name_query=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not name_query:
            raise ValueError(
                "Usage: scrapy crawl flogisticssameday_co_uk -a name_query='Mia khalifa'"
            )

        self.name_query = name_query
        self.slug = self._slugify(self.name_query)
        self.headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-GB,en;q=0.9",
            "priority": "u=0, i",
            "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        }
        self.cookies = {"cfdubsqai": "famer", "popcashpu": "1"}

    def _slugify(self, text):
        """Convert text to lowercase, replace non-alphanumeric with '-', and strip '-'"""
        return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

    def start_requests(self):
        search_url = f"https://f.logisticssameday.co.uk/search/{self.slug}/"
        yield scrapy.Request(
            search_url, headers=self.headers, cookies=self.cookies, callback=self.parse
        )

    def parse(self, response):
        all_tags = response.xpath('//div[@class="author-content"]/a')
        for tag in all_tags:
            _title = tag.xpath("./text()").get()
            model_url = tag.xpath("./@href").get()

            title = self._slugify(_title) if _title else ""
            if self.slug in title:
                yield scrapy.Request(
                    model_url,
                    headers=self.headers,
                    cookies=self.cookies,
                    callback=self.parse_model,
                )

    def parse_model(self, response):
        images = response.xpath('//div[@id="content"]//img/@src').getall()
        yield {
            "page_url": response.url,
            "image": images
        }

        next_page = response.xpath('//div[@id="next_page"]/a/@href').get()
        if next_page:
            yield scrapy.Request(
                next_page,
                headers=self.headers,
                cookies=self.cookies,
                callback=self.parse_model,
            )
