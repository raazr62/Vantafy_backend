import scrapy
import re

class GifhqComSpider(scrapy.Spider):
    name = "gifhq.com"
    emails = ["abuse@gifhq.com", "abuse@flokinet.is"]

    def __init__(self, name_query=None, *args, **kwargs):
        super(GifhqComSpider, self).__init__(*args, **kwargs)
        if not name_query:
            raise ValueError(
                "Please provide a name_query argument, e.g. -a name_query='Ariana Grande' "
                "or multiple: -a name_query='Ariana Grande, Selena Gomez'"
            )

        self.name_query = name_query

    def clean(self, text):
        return re.sub(r"[^a-z0-9]+", "", text.lower()).strip("-")

    def start_requests(self):
        name = self.name_query.replace(" ", "")
        # for name in self.name_queries:
        url = f"https://gifhq.com/backend.php?&p=1&device=pc&r=&sort=&period=&content=all&sourced=0&windowHeight=310&search={name}&post=&sources="
        yield scrapy.Request(
            url=url, callback=self.parse, meta={"page": 1, "name": name}
        )

    def parse(self, response):
        page = response.meta["page"]
        name = response.meta["name"]
        post_link = response.xpath('.//div[@class="card video-card"]')
        if not post_link:
            return
        else:
            for post in post_link:
                href_link = post.xpath('.//a[@rel="noreferrer"]/@href').get()
                v_text = post.xpath('.//h5[@class="card-title"]/a/text()').get()
                teg_text = post.xpath('.//p[@class="card-text"]/a/text()').get()

                if self.clean(name) in self.clean(v_text) or self.clean(name) in self.clean(teg_text) and href_link:
                    id = href_link.split("/")[-1]
                    url = f"https://savemp4.red/backend.php?url=https://gifhq.com/post/{id}"
                    yield scrapy.Request(url=url, callback=self.parse_post)

        next_page = page + 1
        url = f"https://gifhq.com/backend.php?&p={next_page}&device=pc&r=&sort=&period=&content=all&sourced=0&windowHeight=310&search={name}&post=&sources="
        yield scrapy.Request(
            url=url, callback=self.parse, meta={"page": next_page, "name": name}
        )

    def parse_post(self, response):

        video = response.xpath('.//a[@referrerpolicy="origin"]/@href').get()
        img = response.xpath('.//video[@class="card-img-top"]/@poster').get()
        yield {
            "page_url": response.url,
            "image": img,
            "video": video
        }
