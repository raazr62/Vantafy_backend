import scrapy


class BaddiehubComSpider(scrapy.Spider):
    name = "baddiehub.com"
    emails = ["abuse@iqweb.io"]

    def __init__(self, name_query=None, *args, **kwargs):
        super(BaddiehubComSpider, self).__init__(*args, **kwargs)
        self.emails = ["abuse@iqweb.io"]
        if not name_query:
            raise ValueError(
                "Please provide a name_query argument, e.g. -a name_query='Ariana Grande' "
                "or multiple: -a name_query='Ariana Grande, Selena Gomez'"
            )
        self.name_query = name_query

        # Handle multiple names (comma-separated or list-like)
        if isinstance(name_query, str):
            # Split by comma and clean up spaces
            names = [n.strip().lower().replace(" ", "+") for n in name_query.split(",")]
        elif isinstance(name_query, (list, tuple)):
            names = [str(n).strip().lower().replace(" ", "+") for n in name_query]
        else:
            raise ValueError("name_query must be a string or list")

        self.name_queries = names

    def start_requests(self):
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0"
            )
        }

        for name in self.name_queries:
            url = f"https://baddiehub.com/?s={name}"
            yield scrapy.Request(
                url=url,
                headers=headers,
                callback=self.parse,
                meta={"page": 1, "name_query": name},
            )

    def parse(self, response):
        model_name = response.url.split("=")[-1].replace("+", " ").title()
        post_link = response.xpath(
            f'.//a[contains(@title,"{model_name}")]/@href'
        ).getall()
        for link in post_link:
            yield scrapy.Request(
                url=response.urljoin(link),
                headers=response.request.headers,
                callback=self.parse_post,
                meta={"name_query": response.meta["name_query"]},
            )

    def parse_post(self, response):
        video_urls = response.xpath('.//meta[@itemprop="contentURL"]/@content').getall()
        img_urls = response.xpath('.//meta[@itemprop="thumbnailUrl"]/@content').getall()
        yield {"image": img_urls, "video": video_urls}
