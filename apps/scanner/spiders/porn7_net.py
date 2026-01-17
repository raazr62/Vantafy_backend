import scrapy
import re
import urllib.parse


class Porn7NetSpider(scrapy.Spider):
    name = "porn7.net"
    emails = ["abuse@global-layer.com"]

    def __init__(self, name_query=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not name_query:
            raise ValueError(
                "Usage: scrapy crawl porn7_dot_net -a name_query='Mia Khalifa'"
            )

        self.name_query = name_query
        self.slug = self._slugify(self.name_query)
        self.encoded_query = urllib.parse.quote_plus(self.name_query).lower()
        self.last_urls = set()

    def _slugify(self, text):
        return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

    def start_requests(self):
        search_url = f"https://porn7.net/search?q={self.encoded_query}"
        yield scrapy.Request(search_url, callback=self.parse)

    def parse(self, response):
        page = response.meta.get("page", 1)
        all_tags = response.xpath('//a[@class="slider_init_href"]')
        current_urls = {tag.xpath("./@href").get() for tag in all_tags}
        if current_urls == self.last_urls:
            self.logger.info(f"Stopping at page {page}: Same data repeating.")
            return

        self.last_urls = current_urls

        for tag in all_tags:
            _title = tag.xpath("./img/@alt").get()
            post_url = tag.xpath("./@href").get()

            title = self._slugify(_title) if _title else ""
            if self.slug in title:
                yield scrapy.Request(post_url, callback=self.parse_post)

        if not all_tags:
            return

        next_page = page + 1
        next_url = f"https://porn7.net/search-page/{next_page}?nsfw%5B%5D=0&types%5B%5D=image&types%5B%5D=video&types%5B%5D=gallery&slider=1&jsload=1&q={self.encoded_query}"
        yield scrapy.Request(next_url, meta={"page": next_page}, callback=self.parse)

    def parse_post(self, response):
        image_url = response.xpath('//div[@class="sh-section__image"]/img/@src').get()
        video_url = response.xpath(
            '//div[@class="sh-section__image"]//video/source/@src'
        ).get()
        thumbnail = response.xpath(
            '//div[@class="sh-section__image"]//video/@poster'
        ).get()
        if image_url:
            yield {"image": image_url}
        elif video_url:
            yield {"image": thumbnail, "video": video_url}
