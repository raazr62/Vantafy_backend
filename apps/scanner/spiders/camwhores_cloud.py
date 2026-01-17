import scrapy
import re

class CamwhoresCloudSpider(scrapy.Spider):
    name = "camwhores.cloud"
    emails = ["dmca@camwhores.email", "email@buckyemail.com", "ant1xrist76@gmail.com"]
    custom_settings = {
        "DOWNLOAD_DELAY": 1,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "CONCURRENT_REQUESTS": 2,
        "RETRY_TIMES": 1,
        "DOWNLOAD_TIMEOUT": 20,
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0",
    }

    def __init__(self, name_query=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not name_query:
            raise ValueError(
                "Usage: scrapy crawl camwhore_dot_cloud -a name_query='caylin'"
            )

        self.name_query = name_query.strip().lower()
        self.slug = self._slugify(self.name_query)

    def _slugify(self, text):
        return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

    def start_requests(self):
        search_url = f"https://www.camwhores.cloud/search/{self.slug}/"
        yield scrapy.Request(search_url, callback=self.parse)

    def parse(self, response):
        # Normal video items
        video_tags = response.xpath(
            './/div[@id="list_videos_videos_list_search_result_items"]/div/a'
        )

        for tag in video_tags:
            video_url = tag.xpath("./@href").get()
            title = tag.xpath("./@title").get()

            if title:
                title_slug = self._slugify(title)
                if self.slug in title_slug:
                    yield scrapy.Request(video_url, callback=self.detail_page)

        # Albums section
        albums = response.xpath('.//div[@class="list-albums"]')

        for album in albums:
            title = album.xpath(".//a/@title").get()
            title_slug = self._slugify(title)

            if self.slug in title_slug:
                url = album.xpath(".//a/@href").get()
                yield scrapy.Request(url, callback=self.parse_album)

        # Pagination #1 (videos)
        next_number = response.xpath(
            '(.//li[@class="next"]/a/@data-parameters)[position()=1]'
        ).get()

        if next_number:
            m = re.search(r"from_videos\+from_albums:(\d+)", next_number)
            if m:
                match_number = int(m.group(1))
                next_url = f"https://camwhores.cloud/search/{self.slug}/?mode=async&function=get_block&block_id=list_videos_videos_list_search_result&q={self.name_query}&category_ids=&sort_by=&from_videos={match_number}"

                yield scrapy.Request(next_url, callback=self.parse)

        # Pagination #2 (albums)
        next_album = response.xpath(
            '(.//li[@class="next"]/a/@data-parameters)[position()=2]'
        ).get()

        if next_album:
            match = re.search(r"from_videos\+from_albums:(\d+)", next_album)
            if match:
                match_number_album = int(match.group(1))
                next_url = f"https://camwhores.cloud/search/{self.slug}/?mode=async&function=get_block&block_id=list_albums_albums_list_search_result&q={self.name_query}&category_ids=&sort_by=&from_albums={match_number_album}"
                yield scrapy.Request(next_url, callback=self.parse)

    def detail_page(self, response):
        video = response.xpath('//input[@id="share_link"]/@value').get()
        preview = response.xpath('//meta[@property="og:image"]/@content').get()
        thumbnails = response.xpath(
            './/div[@class="block-screenshots"]/a/@href'
        ).getall()

        if not thumbnails:
            thumbnails = response.xpath(
                './/div[@class="block-screenshots"]//img/@data-original'
            ).getall()

        if preview:
            images = thumbnails + [preview]
            yield {"image": images, "video": video}
        else:
            yield {"image": thumbnails, "video": video}

    def parse_album(self, response):
        images = response.xpath(
            './/div[@class="album-holder"]/div[@class="images"]/a/@href'
        ).getall()
        yield {"video": response.url, "image": images}
