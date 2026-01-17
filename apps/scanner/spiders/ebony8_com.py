import scrapy
import re

class Ebony8ComSpider(scrapy.Spider):
    name = "ebony8.com"
    emails = ["dmcalegalreport@gmail.com", "abuse@ovh.net"]

    def __init__(self, name_query=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not name_query:
            raise ValueError(
                "Usage: scrapy crawl fapomania_dot_com -a name_query='Demi Lovato'"
            )
        self.name_query = name_query
        self.slug = self.clean(self.name_query)

    def clean(self, text):
        """Convert text to lowercase, replace non-alphanumeric with '-', and strip '-'"""
        return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

    def start_requests(self):
        search_url = f"https://www.ebony8.com/search/{self.slug}/"
        yield scrapy.Request(search_url, callback=self.parse)

    def parse(self, response):
        data = response.xpath('.//div[@class="list-videos"]//div[@class="item  "]/a')
        for i in data:
            title = i.xpath(".//@title").get()
            if self.clean(self.name_query) in self.clean(title):
                url = i.xpath(".//@href").get()
                yield scrapy.Request(url=url, callback=self.parse_video)
        # Pagination #1 (videos)
        next_number = response.xpath(
            '(.//li[@class="next"]/a/@data-parameters)[position()=1]'
        ).get()

        if next_number:
            m = re.search(r"from_videos\+from_albums:(\d+)", next_number)
            if m:
                num = int(m.group(1))
                next_url = f"https://www.ebony8.com/search/{self.slug}/?mode=async&function=get_block&block_id=list_videos_videos_list_search_result&q={self.name_query}&category_ids=&sort_by=&from_videos={num}"
                yield scrapy.Request(next_url, callback=self.parse)

        # Albums section
        albums = response.xpath('.//div[@class="list-albums"]/a')
        if albums:
            for album in albums:
                title = album.xpath(".//@title").get()
                title_slug = self.clean(title)

                if self.slug in title_slug:
                    url = album.xpath(".//@href").get()
                    yield scrapy.Request(url, callback=self.parse_album)

            next_album = response.xpath(
                '(.//li[@class="next"]/a/@data-parameters)[position()=2]'
            ).get()

            if next_album:
                match = re.search(r"from_videos\+from_albums:(\d+)", next_album)
                if match:
                    num_album = int(match.group(1))
                    next_url = f"https://www.ebony8.com/search/{self.slug}/?mode=async&function=get_block&block_id=list_albums_albums_list_search_result&q={self.name_query}&category_ids=&sort_by=&from_albums={num_album}"
                    yield scrapy.Request(next_url, callback=self.parse)

    def parse_video(self, response):
        image_url = response.xpath('.//meta[@property="og:image"]/@content').get()
        yield {"video": response.url, "image": image_url}

    def parse_album(self, response):
        images = response.xpath('.//div[@class="images"]/a/@href').getall()
        yield {"video": response.url, "image": images}
