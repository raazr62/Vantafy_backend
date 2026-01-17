import scrapy
import urllib.parse
import re

class FigToSpider(scrapy.Spider):
    name = "fig.to"
    emails = ["abuse@koddos.com"]

    def __init__(self, name_query = None, **kwargs):
        super().__init__(name_query, **kwargs)
        if not name_query:
            raise ValueError(
                "Please provide a name_query argument, e.g. -a name_query='Ariana Grande' "
                "or multiple: -a name_query='Ariana Grande, Selena Gomez'"
            )

        self.name_query = name_query

    def start_requests(self):
        encoded_query = urllib.parse.quote(self.name_query)
        url = f"https://fig.to/?s={encoded_query}"
        headers = {
            "accept": "text/plain, */*; q=0.01",
            "referer": "https://fig.to/",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
        }

        yield scrapy.Request(url=url,headers=headers,callback=self.parse)

    def clean(self, text):
        # lowercase + keep only letters & numbers
        return re.sub(r"[^a-z0-9]+", "", text.lower())

    def parse(self,response):
        data = response.xpath('.//li[@class="g1-collection-item"]/article//h2/a')
        for i in data:
            title = i.xpath('.//text()').get()
            if self.clean(self.name_query) in self.clean(title):
                post_url = i.xpath('.//@href').get()
                encoded_query = urllib.parse.quote(self.name_query)
                headers = {
                    "sec-ch-ua-platform": '"macOS"',
                    "Referer": response.url,
                    "X-Requested-With": "XMLHttpRequest",
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
                    "Accept": "*/*",
                    "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
                    "sec-ch-ua-mobile": "?0",
                }
                yield scrapy.Request(post_url,headers=headers, callback=self.parse_post)

        next_page = response.xpath(
            ".//a[@data-g1-next-page-url]/@data-g1-next-page-url"
        ).get()
        if next_page:
            encoded_query = urllib.parse.quote(self.name_query)
            headers = {
                "sec-ch-ua-platform": '"macOS"',
                "Referer": f"https://fig.to/?s='{encoded_query}'",
                "X-Requested-With": "XMLHttpRequest",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
                "Accept": "*/*",
                "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
                "sec-ch-ua-mobile": "?0",
            }
            yield scrapy.Request(next_page,headers=headers,callback=self.parse)

    def parse_post(self, response):
        image = response.xpath(
            './/meta[@property="og:image:secure_url"]/@content'
        ).get()

        gallary = response.xpath(
            './/figure[@class="mace-gallery-teaser"]/@data-g1-gallery'
        ).get()
        if gallary:
            urls = re.findall(
                r'https:\\/\\/fig18\.famousinternetgirls\.com\\/images\\/[^"]+?\.jpg',
                gallary,
            )
            urls = list(set(urls))
            all_images = urls + [image]
            yield {"video": response.url, "image": all_images}
        else:
            yield {"video": response.url, "image": image}
