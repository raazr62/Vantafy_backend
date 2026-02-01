import scrapy
import re
import json
from scrapy.utils.response import open_in_browser


class HardgifComSpider(scrapy.Spider):
    name = "hardgif.com"
    emails = ["abuse@hardgif.com", "abuse@flokinet.is"]

    def __init__(self, name_query=None, *args, **kwargs):
        super(HardgifComSpider, self).__init__(*args, **kwargs)
        if not name_query:
            raise ValueError(
                "Please provide a name_query argument, e.g. -a name_query='Ariana Grande' "
                "or multiple: -a name_query='Ariana Grande, Selena Gomez'"
            )

        self.name_query = name_query

    def clean(self, text):
        # lowercase + keep only letters & numbers
        return re.sub(r"[^a-z0-9]+", "", text.lower())

    def start_requests(self):
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/142.0.0.0 Safari/537.36"
            )
        }
        name = self.name_query.replace(" ", "").title()
        url = f"https://hardgif.com/backend.php?&p=1&search={name}"

        yield scrapy.Request(
            url=url,
            callback=self.parse,
            headers=headers,
            meta={"page": 1, "name": name},
        )

    def parse(self, response):
        # open_in_browser(response)
        page = response.meta["page"]
        name = response.meta["name"]

        posted_videos = response.xpath(
            './/div[@class="video"] | .//img[@class="img albumPhoto lazy"]'
        )

        for video in posted_videos:

            username = video.xpath(
                './/div[@class="bottom"]/a/text() | .//parent::a/following-sibling::div/a/text()'
            ).get()
            video_text = video.xpath(".//video/@title | .//@alt").get()

            if self.clean(name) in self.clean(video_text) or self.clean(
                name
            ) in self.clean(username):

                page_url_id = video.xpath(".//@data-post-id").get()

                page_url = f"https://hardgif.com/gif/{page_url_id}"

                thumbnel = video.xpath(
                    './/video[@referrepolicy="noreferrer"]/@data-poster'
                ).get()

                if not thumbnel:

                    img = video.xpath(".//@data-duplicates-thumbs").getall()

                    for item in img:
                        if not item or not item.strip():
                            continue

                        try:
                            urls = json.loads(item)
                        except json.JSONDecodeError:
                            self.logger.error(
                                f"Invalid JSON in data-duplicates-thumbs: {item!r}"
                            )
                            continue

                        # Append full URLs
                        yield {
                            "page_url": page_url,
                            "image": [f"https://hardgif.com{u}" for u in urls],
                            
                        }
                video = video.xpath(
                    './/video[@referrepolicy="noreferrer"]/source/@data-src'
                ).get()

                yield {
                    "page_url": page_url,
                    "image": thumbnel,
                    "video": video
                }

                next_page = page + 1
                url = f"https://hardgif.com/backend.php?&p={next_page}&search={name}"
                yield scrapy.Request(
                    url=url,
                    callback=self.parse,
                    headers=response.request.headers,
                    meta={"page": next_page, "name": name},
                )
