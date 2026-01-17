import scrapy

class FapelloRuSpider(scrapy.Spider):
    name = "fapello.ru"
    emails = ["abuse@koddos.com"]

    def __init__(self, name_query=None, *args, **kwargs):
        super(FapelloRuSpider, self).__init__(*args, **kwargs)
        super().__init__(*args, **kwargs)

        if not name_query:
            raise ValueError(
                "Provide a name_query. Example: -a name_query='Angela White'"
            )
            
        self.name_query = name_query
        
        # Multiple names support
        if isinstance(name_query, str):
            names = [n.strip().lower().replace(" ", "-") for n in name_query.split(",")]
        elif isinstance(name_query, (list, tuple)):
            names = [str(n).strip().lower().replace(" ", "-") for n in name_query]
        else:
            raise ValueError("name_query must be a string or list")

        self.name_queries = names

    def start_requests(self):
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/142.0.0.0 Safari/537.36"
            )
        }

        for name in self.name_queries:
            url = f"https://fapello.ru/galleries/{name}-onlyfans-photo-gallery"
            yield scrapy.Request(
                url=url,
                headers=headers,
                callback=self.parse_photo_galleries,
                meta={"page": 1, "name_query": name},
            )
            v_url = f"https://fapello.ru/models/{name}/videos"
            yield scrapy.Request(
                url=v_url,
                headers=headers,
                callback=self.parse_video_galleries,
                meta={"page": 1, "name_query": name},
            )

    def parse_video_galleries(self, response):

        video_urls = response.xpath('.//div[@id="videos-content"]//a/@href').getall()
        imges = response.xpath('.//div[@id="videos-content"]//a/img/@src').getall()

        # yield {"image": response.urljoin(imges), "video": response.urljoin(video_urls)}
        for video_url, img in zip(video_urls, imges):
            yield {
                "image": response.urljoin(img),
                "video": response.urljoin(video_url),
            }

    def parse_photo_galleries(self, response):
        name = response.meta["name_query"].replace("+", " ").title()
        img_urls = response.xpath('.//img[@itemprop="thumbnail"]/@src').getall()
        yield {"image": img_urls, "video": []}

        next_page = response.xpath('.//a[@rel="next"]/@href').get()
        if next_page:
            yield scrapy.Request(
                url=response.urljoin(next_page),
                headers=response.request.headers,
                callback=self.parse_photo_galleries,
                meta={"name_query": response.meta["name_query"]},
            )
