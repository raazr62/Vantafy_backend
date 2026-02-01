import scrapy
import urllib.parse
import re

class LeaknudesComSpider(scrapy.Spider):
    name = "leaknudes.com"
    emails = ["leaknudes.j5lxe@simplelogin.com", "abuse@ddos-guard.net"]

    def __init__(self, name_query=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not name_query:
            raise ValueError(
                "Please provide a name_query argument, e.g. -a name_query='Ariana Grande'"
            )
        self.name_query = name_query

    def start_requests(self):
        encoded_query = urllib.parse.quote(self.name_query)
        url = f"https://leaknudes.com/search/{encoded_query}"
        headers = {
            "accept": "*/*",
            "accept-language": "en-GB,en;q=0.9",
            "x-requested-with": "XMLHttpRequest",
            "referer": "https://leaknudes.com",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        }
        yield scrapy.Request(url=url, headers=headers, callback=self.parse)

    def clean(self, text):
        # lowercase + keep only letters & numbers
        return re.sub(r"[^a-z0-9]+", "", text.lower())

    def parse(self, response):
        data = response.xpath('.//section[@id="infinite-container"]/article/a')
        for i in data:
            title = i.xpath(".//img/@alt").get()
            if self.clean(self.name_query) in self.clean(title):
                url = i.xpath(".//@href").get()
                yield scrapy.Request(
                    url=response.urljoin(url), callback=self.parse_videos
                )

        next_page = response.xpath(
            './/div[@id="post_pagination"]//span[@class="current pagenum"]/following-sibling::a[1]/@href'
        ).get()
        if next_page:
            yield scrapy.Request(url=response.urljoin(next_page), callback=self.parse)

    def parse_videos(self, response):
        # for album images
        images = response.xpath('.//section[@class="posts "]//img/@data-src').getall()
        video = []

        # for videos
        if not images:
            images = response.xpath('.//video[@id="my-video"]/@poster').getall()
            video = response.xpath('.//source[@type="video/mp4"]/@src').get()

        if video or images:
            yield {
                "page_url": response.url,
                "video": video,
                "image": [response.urljoin(image) for image in images],
            }
