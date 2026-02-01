import scrapy

class FappeningbookComSpider(scrapy.Spider):
    name = "fappeningbook.com"
    emails = ["lopapopator@gmail.com"]
    def __init__(self, name_query=None, *args, **kwargs):
        super(FappeningbookComSpider, self).__init__(*args, **kwargs)
        if not name_query:
            raise ValueError(
                "Please provide a name_query argument, e.g. -a name_query='Ariana Grande'"
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

    def start_requests(self):

        for name in self.name_queries:
            urls = [
                f"https://fappeningbook.com/{name}-nude/"
            ]
            for url in urls:
                yield scrapy.Request(
                    url=url,
                    callback=self.parse,
                )

    def parse(self, response):
        imgs = response.xpath(
            './/img[@alt=" Nude"]/@src | .//img[@itemprop="thumbnail"]/@src'
        ).getall()

        page_urls = response.xpath(
            '(.//div[@class="shrt-blk"])[1]/div/a/@href'
        ).getall()

        yield {"page_url": page_urls, "image": imgs}

        next_page = response.xpath('.//a[text()="Next "]/@href').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)
