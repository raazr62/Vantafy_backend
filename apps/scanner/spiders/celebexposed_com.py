import scrapy
import re
import urllib.parse


class CelebexposedComSpider(scrapy.Spider):
    name = "celebexposed.com"
    emails = [
        "contact@of.celebexposed.com ",
        "abuse@koddos.com",
        "d6c77ad0dcaa43718639516547acf735.protect@withheldforprivacy.com",
    ]

    custom_settings = {"CONCURRENT_REQUESTS": 1, "TELNETCONSOLE_ENABLED": False}

    def __init__(self, name_query=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not name_query:
            raise ValueError(
                "Usage: scrapy crawl celebexpose_dot_com -a name_query='Fadinha Maju'"
            )

        self.name_query = name_query
        self.slug = self._slugify(self.name_query)
        self.encoded_query = urllib.parse.quote(name_query)

    def _slugify(self, text):
        return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

    def start_requests(self):
        search_url = f"https://celebexposed.com/search/{self.slug}"
        yield scrapy.Request(search_url, callback=self.parse)

    def parse(self, response):
        all_urls = []
        all_user = response.xpath(
            '//div[@class="bg-red-400 max-w-full lg:h-56 h-48 rounded-lg relative overflow-hidden shadow uk-transition-toggle"]/a/@href'
        ).getall()
        for user in all_user:
            if "/babe/" in user:
                model_url = user.replace("/babe/", "/").strip()
                all_urls.append(model_url)
            else:
                all_urls.append(user)

        unique_urls = list(set(all_urls))
        for url in unique_urls:
            yield scrapy.Request(url, callback=self.parse_detail)

    def parse_detail(self, response):
        if "/ajax/" not in response.url:
            title_head = response.xpath(
                '//p[@class="flex font-semibold mb-3 space-x-2  dark:text-gray-10"]/text()'
            ).get()
            if title_head:
                title = self._slugify(title_head)
                if self.slug not in title:
                    return

            pages = response.xpath('//div[@id="showmore"]/@data-max').get()
            if pages:
                pages = int(pages)
                for i in range(pages, 1, -1):
                    page_url = (
                        f"https://celebexposed.com/ajax/model/{title}/page-{i}/query"
                    )
                    yield scrapy.Request(page_url, callback=self.parse_detail)

        images = response.xpath(
            '//img[@class="w-full h-full absolute object-cover inset-0"]/@src'
        ).getall()

        yield {"image": images,"video":[]}
