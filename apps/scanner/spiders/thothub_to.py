import scrapy
import urllib.parse
import re


class ThothubToSpider(scrapy.Spider):
    name = "thothub.to"
    emails = ["abuse@medera.cloud", "abuse@v-sys.org"]

    def __init__(self, name_query=None, *args, **kwargs):
        super(ThothubToSpider, self).__init__(*args, **kwargs)
        if not name_query:
            raise ValueError(
                "Please provide a name_query argument, e.g.:  -a name_query='Ariana Grande'  "
            )
        self.name_query = name_query
        encoded_query = urllib.parse.quote(name_query)
        self.start_urls = [f"https://thothub.to/search/{encoded_query}/"]

    def start_requests(self):
        headers = {
            "accept": "text/plain, */*; q=0.01",
            "accept-language": "en-US,en;q=0.9",
            "priority": "u=1, i",
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

    def clean(self, text):
        # lowercase + keep only letters & numbers
        return re.sub(r"[^a-z0-9]+", "", text.lower())

    def parse(self, response):
        public_urls = response.xpath(
            './/div[@id="list_videos_videos_list_search_result_items"]/div'
        )
        if public_urls:
            for i in public_urls:
                # text = i.xpath(".//a/@title").get()
                # if self.name_query.lower() in text.lower():
                url = i.xpath(".//a/@href").get()
                yield scrapy.Request(url=url, callback=self.parse_video)

        albums = response.xpath('.//div[@class="list-albums"]')
        if albums.xpath(".//a"):
            for i in albums:
                # text = i.xpath(".//a/@title").get()
                # if self.name_query.lower() in text.lower():
                url = i.xpath(".//a/@href").get()
                yield scrapy.Request(url=url, callback=self.parse_album)

        next_page_video = response.xpath(
            './/li[@class="next"]/a[@data-block-id="list_videos_videos_list_search_result"]/@data-parameters'
        ).get()
        if next_page_video:
            page_num = next_page_video.split(":")[-1]
            n_url = f"{self.start_urls[0]}?mode=async&function=get_block&block_id=list_videos_videos_list_search_result&q={self.name_query}&category_ids=&sort_by=&from_videos={page_num}"
            yield scrapy.Request(url=n_url, callback=self.parse)

        next_page_album = response.xpath(
            './/li[@class="next"]/a[@data-block-id="list_albums_albums_list_search_result"]/@data-parameters'
        ).get()
        if next_page_album:
            page_num = next_page_album.split(":")[-1]
            na_url = f"{self.start_urls[0]}?mode=async&function=get_block&block_id=list_albums_albums_list_search_result&q={self.name_query}&category_ids=&sort_by=&from_albums={page_num}"
            yield scrapy.Request(url=na_url, callback=self.parse)

    def parse_video(self, response):
        name_query = self.name_query
        tegs = response.xpath(
            './/div[@class="item"][contains(text(),"Tags")]/a/text()'
        ).getall()
        tegs = " ".join(tegs)
        video_text = response.xpath('.//div[@class="headline"]/h1/text()').get()
        images = response.xpath('.//div[@class="block-screenshots"]/a/@href').getall()

        if not images:
            images = response.xpath(
                './/div[@class="block-screenshots"]//img/@data-original'
            ).getall()
        if self.clean(name_query) in self.clean(video_text) or self.clean(
            name_query
        ) in self.clean(tegs):
            yield {"video": response.url, "image": images}

    def parse_album(self, response):
        images = response.xpath(
            './/div[@class="album-holder"]/div[@class="images"]/a/@href'
        ).getall()
        yield {"page_url": response.url, "image": images}
