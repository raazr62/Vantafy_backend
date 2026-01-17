import scrapy
import re


class BaddiesonlyTvSpider(scrapy.Spider):
    name = "baddiesonly.tv"
    emails = ["dmca.BaddiesOnly.TV@gmail.com","abuses@abelohost.net"]
    
    def __init__(self, name_query=None, *args, **kwargs):
        super(BaddiesonlyTvSpider, self).__init__(*args, **kwargs)
        if not name_query:
            raise ValueError(
                "Please provide a name_query argument, e.g. -a name_query='Ariana Grande' "
                "or multiple: -a name_query='Ariana Grande, Selena Gomez'"
            )
        self.name_query = name_query

        # Handle multiple names (comma-separated or list-like)
        if isinstance(name_query, str):
            # Split by comma and clean up spaces
            names = [n.strip().lower().replace(" ", "-") for n in name_query.split(",")]
        elif isinstance(name_query, (list, tuple)):
            names = [str(n).strip().lower().replace(" ", "-") for n in name_query]
        else:
            raise ValueError("name_query must be a string or list")

        self.name_queries = names

    def clean(self, text):
        # lowercase + keep only letters & numbers
        return re.sub(r"[^a-z0-9]+", "", text.lower())

    def start_requests(self):
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0"
            )
        }

        for name in self.name_queries:
            url = f"https://baddiesonly.tv/search/{name}/"
            yield scrapy.Request(
                url=url,
                headers=headers,
                callback=self.parse,
                meta={"page": 1, "name_query": name},
            )

    def parse(self, response):
        post_links = response.xpath('.//div[@class="item  "]/a/@href').getall()

        for link in post_links:

            yield scrapy.Request(
                url=response.urljoin(link),
                headers=response.request.headers,
                callback=self.parse_post,
                meta={"name_query": response.meta["name_query"]},
            )

    def parse_post(self, response):

        name_query = response.meta.get("name_query")
        text = response.xpath('.//div[@class="video-h1-show"]//text()').get()
        tegs = response.xpath('.//div[contains(text(),"Tags:")]/a/text()').getall()
        tegs = " ".join(tegs)
        if self.clean(name_query) not in self.clean(text) and self.clean(
            name_query
        ) not in self.clean(tegs):
            return

        img_urls = response.xpath('.//div[@class="block-screenshots"]/a/@href').getall()
        yield {"image": img_urls, "video": response.url}
