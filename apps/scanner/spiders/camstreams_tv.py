import scrapy
import re
import urllib.parse


class CamstreamsTvSpider(scrapy.Spider):
    name = "camstreams.tv"
    emails = ["abuse@sharktech.net"]

    custom_settings = {"TELNETCONSOLE_ENABLED": False}

    def __init__(self, name_query=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not name_query:
            raise ValueError("Usage: scrapy crawl camstreams_tv -a name_query='caylin'")

        self.name_query = name_query
        self.slug = self._slugify(self.name_query)
        self.encoded_query = urllib.parse.quote(name_query)

    def _slugify(self, text):
        return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

    def start_requests(self):
        search_url = f"https://camstreams.tv/search/{self.encoded_query}/"
        yield scrapy.Request(search_url, callback=self.parse)

    def parse(self, response):
        video_tags = response.xpath(
            '//div[@class="list-videos"]//div[@class="item  "]/a'
        )
        if video_tags:
            for tag in video_tags:
                video_url = tag.xpath("./@href").get()
                title = tag.xpath("./@title").get()
                title_slug = self._slugify(title)

                if self.slug in title_slug:
                    yield scrapy.Request(video_url, callback=self.detail_page)

        load_next = response.xpath('//div[@class="load-more"]/a')
        if load_next:
            page_parameter = load_next.xpath(".//@data-parameters").get()
            match = re.search(r"from_videos\+from_albums:(\d+)", page_parameter)
            if match:
                page_number = int(match.group(1))
                next_url = f"https://camstreams.tv/search/{self.slug}/?from_videos={page_number}"
                yield scrapy.Request(next_url, callback=self.parse)

    def detail_page(self, response):
        ll = []
        preview = response.xpath('//meta[@property="og:image"]/@content').get()
        if preview:
            ll.append(preview)
        thumbnails = response.xpath(
            '//div[@class="block-screenshots"]/a/img/@data-original'
        ).getall()
        if thumbnails:
            ll.extend(thumbnails)

        main_video = response.xpath('//input[@id="share_link"]/@value').get()

        yield {
            "page_url": response.url,
            "image": ll,
            "video": main_video
        }
