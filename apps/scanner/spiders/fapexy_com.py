import scrapy
import urllib.parse

class FapexyComSpider(scrapy.Spider):
    name = "fapexy.com"
    emails = ["fapexyweb@gmail.com", "abuse@serverel.com"]

    custom_settings = {
        "DOWNLOAD_DELAY": 1,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "CONCURRENT_REQUESTS": 4,
        "RETRY_TIMES": 1,
        "DOWNLOAD_TIMEOUT": 20,
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0",
    }

    def __init__(self, name_query=None, *args, **kwargs):
        super(FapexyComSpider, self).__init__(*args, **kwargs)
        if not name_query:
            raise ValueError(
                "Please provide a name_query argument, e.g. -a name_query='Ariana Grande'"
            )
        self.name_query = name_query
        encoded_query = urllib.parse.quote(name_query)
        self.start_urls = [f"https://fapexy.com/search/{encoded_query}/"]

    def start_requests(self):
        headers = {
            "accept": "text/plain, */*; q=0.01",
            "accept-language": "en-US,en;q=0.9",
            "priority": "u=1, i",
            "referer": f"https://fapexy.com/",
            "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
            "x-requested-with": "XMLHttpRequest",
        }
        yield scrapy.Request(
            url=self.start_urls[0], headers=headers, callback=self.parse
        )

    def parse(self, response):
        data = response.xpath(
            './/div[@class="search-results card card-style shadow-l"]'
        )
        for i in data:
            url = i.xpath(".//a/@href").get()
            name = i.xpath(".//p/text()").get()

            if self.name_query.lower() in name.lower():
                yield scrapy.Request(
                    url=url, callback=self.parse_profile, meta={"page": 1}
                )

    def parse_profile(self, response):
        page = response.meta.get("page", 1)

        # Collect all image URLs from current page
        image_urls = response.xpath('.//div[@id="media"]//a/@href').getall()
        for img in image_urls:
            yield scrapy.Request(url=img, callback=self.parse_image)

        # Build next-page URL
        # Current profile URL structure: https://fapexy.com/model/mia-khalifa/
        # AJAX URL pattern: https://fapexy.com/ajax/model/mia-khalifa/page-2/
        base = response.url.rstrip("/")
        profile_slug = base.split("/")[-1]
        next_page = page + 1

        next_page_url = (
            f"https://fapexy.com/ajax/model/{profile_slug}/page-{next_page}/"
        )

        # Send request to check if next page contains URLs
        yield scrapy.Request(
            url=next_page_url,
            callback=self.parse_next_page,
            meta={"page": next_page, "profile_slug": profile_slug},
        )

    def parse_next_page(self, response):
        page = response.meta.get("page")
        profile_slug = response.meta.get("profile_slug")

        # Extract new page images (same structure: .//a/@href)
        image_urls = response.xpath(".//a/@href").getall()

        # If no URLs found → stop pagination
        if not image_urls:
            return

        # Yield images
        for img in image_urls:
            yield scrapy.Request(url=img, callback=self.parse_image)

        # Continue to next page
        next_page = page + 1
        next_page_url = (
            f"https://fapexy.com/ajax/model/{profile_slug}/page-{next_page}/"
        )

        yield scrapy.Request(
            url=next_page_url,
            callback=self.parse_next_page,
            meta={"page": next_page, "profile_slug": profile_slug},
        )

    def parse_image(self, response):
        image = response.xpath(".//a[@title]/img/@src").get()
        yield {"image": image, "video": []}
