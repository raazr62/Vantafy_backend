import scrapy
import re

class LeakedXxxSpider(scrapy.Spider):
    name = "leak.xxx"
    emails = ["abuse@global-layer.com"]

    def __init__(self, name_query=None, *args, **kwargs):
        super(LeakedXxxSpider, self).__init__(*args, **kwargs)
        if not name_query:
            raise ValueError(
                "Please provide a name_query argument, e.g. -a name_query='Ariana Grande' "
                "or multiple: -a name_query='Ariana Grande, Selena Gomez'"
            )

        self.name_query = name_query

    def clean(self, text):
        return re.sub(r"[^a-z0-9]+", "", text.lower()).strip("-")

    def start_requests(self):
        name = self.name_query.replace(" ", "-").lower()
        name_slug = self.name_query.replace(" ", "+").lower()
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/142.0.0.0 Safari/537.36"
            )
        }

        url = f"https://leak.xxx/search/{name}/"
        yield scrapy.Request(
            url=url,
            headers=headers,
            callback=self.parse,
            meta={"name_query": name, "name_slug": name_slug},
        )

    def parse(self, response):
        name = response.meta["name_query"]
        name_slug = response.meta["name_slug"]

        all_albums = response.xpath(
            './/div[@class="list-albums"]//div[@class="item  "]/a'
        )

        for album in all_albums:
            text = album.xpath(".//@title").get()
            # img = album.xpath('.//img[@class="thumb "]/@src').get()
            album_url = album.xpath(".//@href").get()

            if self.clean(name) in self.clean(text):
                yield scrapy.Request(
                    album_url,
                    callback=self.parse_album,
                    meta={"name_query": name, "name_slug": name_slug},
                )

        all_post = response.xpath(
            './/div[@class="list-videos"]//div[@class="item  "]/a'
        )

        for post in all_post:
            text = post.xpath(".//@title").get()
            img = post.xpath('.//img[@class="thumb "]/@src').get()
            video = post.xpath(".//@href").get()

            if self.clean(name) in self.clean(text):
                yield scrapy.Request(url=video, callback=self.parse_video)

        next_number = response.xpath(
            '(.//li[@class="next"]/a/@data-parameters)[position()=1]'
        ).get()
        if next_number:
            m = re.search(r"from_videos\+from_albums:(\d+)", next_number)
            if m:
                match_number = int(m.group(1))
                next_url = f"https://leak.xxx/search/{name}/?mode=async&function=get_block&block_id=list_videos_videos_list_search_result&q={name_slug}&category_ids=&sort_by=&from_videos={match_number}"
                yield scrapy.Request(
                    next_url,
                    callback=self.parse,
                    meta={"name_query": name, "name_slug": name_slug},
                )
        # Pagination #2 (albums)
        next_album = response.xpath(
            '(.//li[@class="next"]/a/@data-parameters)[position()=2]'
        ).get()
        if next_album:
            match = re.search(r"from_videos\+from_albums:(\d+)", next_album)
            if match:
                match_number_album = int(match.group(1))
                next_url = f"https://leak.xxx/search/{name}/?mode=async&function=get_block&q={name_slug}&category_ids=&sort_by=&from_videos=&from_albums={match_number_album}&block_id=list_albums_albums_list_search_result"
                yield scrapy.Request(
                    next_url,
                    callback=self.parse,
                    meta={"name_query": name, "name_slug": name_slug},
                )

    def parse_album(self, response):
        image = response.xpath('.//div[@class="images"]/a/@href').getall()
        yield {"image": image, "video": []}

    def parse_video(self, response):
        image = response.xpath('.//meta[@property="og:image"]/@content').get()
        yield {"image": image, "video": response.url}
