import scrapy
import json
import urllib.parse

class FindhernameNetSpider(scrapy.Spider):
    name = "findhername.net"
    def __init__(self, name_query=None, *args, **kwargs):
        super(FindhernameNetSpider, self).__init__(*args, **kwargs)
        if not name_query:
            raise ValueError(
                "Please provide a name_query argument, e.g. -a name_query='Ariana Grande'"
            )
        self.name_query = name_query
        encoded_query = urllib.parse.quote(name_query)
        self.start_urls = [
            f"https://findhername.net/suggest/?q={encoded_query}"
        ]

    def start_requests(self):
        headers = {
            "accept": "text/plain, */*; q=0.01",
            "accept-language": "en-US,en;q=0.9",
            "priority": "u=1, i",
            "referer": f'https://findhername.net/search/{self.name_query.replace(" ", "--").lower()}/',
            "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
            "x-requested-with": "XMLHttpRequest",
        }
        yield scrapy.Request(
            url=self.start_urls[0], headers=headers, callback=self.parse
        )

    def parse(self, response):
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.error("Response is not JSON")
            return

        query_lower = self.name_query.lower()
        for item in data["suggestions"]:
            title = item.get("value") or item.get("title") or ""
            if query_lower in title.lower():
                type = item.get("data").get("type")
                url = item.get("data").get("url")
                if type.lower() == "models":
                    self.model_url = url
                    yield scrapy.Request(url, callback=self.parse_videos)

    def parse_videos(self, response):
        urls = response.xpath('.//div[@class="content-section"]/div//a/@href').getall()
        if not urls:
            urls = response.xpath('.//div[@class="thumbs"]//a/@href').getall()
        for i in urls:
            yield scrapy.Request(url=response.urljoin(i), callback=self.parse_ss)

        next_page = response.xpath('.//a[@class="next"]/@data-parameters').get()
        if next_page:
            page_num = next_page.split(":")[-1]
            n_url = f"{self.model_url}?mode=async&function=get_block&block_id=list_videos_common_videos_list&sort_by=post_date&from={page_num}"
            yield scrapy.Request(url=n_url, callback=self.parse_videos)

    def parse_ss(self, response):
        images = response.xpath('.//a[@rel="screenshots"]/@href').getall()
        if not images:
            images = response.xpath(
                './/div[@class="album-inner images"]/a/@href'
            ).getall()
        yield {"page_url": response.url, "image": images}
