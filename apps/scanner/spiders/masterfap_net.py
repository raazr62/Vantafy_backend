import scrapy
import urllib.parse

class MasterfapNetSpider(scrapy.Spider):
    name = "masterfap.net"
    emails = ["dmcamasterfap@protonmail.com", "abuse@koddos.com"]
    def __init__(self, name_query=None, *args, **kwargs):
        super(MasterfapNetSpider, self).__init__(*args, **kwargs)
        if not name_query:
            raise ValueError(
                "Please provide a name_query argument, e.g. -a name_query='Ariana Grande'"
            )
        self.name_query = name_query

        encoded_query = urllib.parse.quote(name_query.lower().replace(' ','-'))
        self.start_urls = [f"https://www.masterfap.net/profile/{encoded_query}/"]

    def start_requests(self):
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-IN,en;q=0.9",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "DNT": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
            "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"'
        }
        yield scrapy.Request(
            url=self.start_urls[0], headers=headers, callback=self.parse
        )

    def parse(self, response):
        image_urls = response.xpath('.//div[@id="content"]//a/@href').getall()
        for url in image_urls:
            yield scrapy.Request(url=url, callback=self.parse_image)

        next_page = response.xpath('.//a[@rel="next"]/@href').get()
        if next_page:
            yield scrapy.Request(url=next_page, callback=self.parse)

    def parse_image(self, response):
        image_url = response.xpath('.//meta[@property="og:image"]/@content').get()
        yield {
            "image": image_url,
            "video":[]
            }
