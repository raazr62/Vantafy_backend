import scrapy

class FapodropComSpider(scrapy.Spider):
    name = "fapodrop.com"
    emails = ["abusedrop@fapodrop.com"]
    def __init__(self, name_query=None, *args, **kwargs):
        super(FapodropComSpider, self).__init__(*args, **kwargs)
        if not name_query:
            raise ValueError(
                "Please provide a name_query argument, e.g.: -a name_query='Bella Thorne'"
            )
        self.name_query = name_query
        self.search_url = "https://fapodrop.com/search"

    def start_requests(self):
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-IN,en-US;q=0.9,en;q=0.8,gu;q=0.7",
            "cache-control": "max-age=0",
            "content-type": "application/x-www-form-urlencoded",
            "dnt": "1",
            "origin": "https://fapodrop.com",
            "priority": "u=0, i",
            "referer": "https://fapodrop.com/search",
            "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/142.0.0.0 Safari/537.36",
        }

        payload = {"searchVal": self.name_query}
        yield scrapy.FormRequest(
            url=self.search_url,
            formdata=payload,
            headers=headers,
            callback=self.parse,
        )

    def parse(self, response):
        urls = response.xpath('.//div[contains(@class,"home-profile")]/div[1]/a')
        for i in urls:
            name = i.xpath(".//text()").get()
            if name and self.name_query.lower() in name.lower():
                url = i.xpath(".//@href").get()
                url = response.urljoin(url)
                yield scrapy.Request(url=url, callback=self.parse_profile)

    def parse_profile(self, response):
        urls = response.xpath('.//div[@class="one-pack"]/a/@href').getall()
        for url in urls:
            if not url:
                continue

            normalized_name = self.name_query.lower().replace(" ", "-")
            clean_name = self.name_query.lower().replace(" ", "")
            original_name = self.name_query.lower()

            # Match any format like bella-thorne, bellathorne, or bella thorne
            if (
                normalized_name in url.lower()
                or clean_name in url.lower()
                or original_name in url.lower()
            ):
                full_url = response.urljoin(url)
                yield scrapy.Request(full_url, callback=self.parse_post)

        next_page = response.xpath('.//a[contains(text(),"Next page")]/@href').get()
        if next_page:
            yield scrapy.Request(
                url=response.urljoin(next_page), callback=self.parse_profile
            )

    def parse_post(self, response):
        """Extract media from each post page"""
        image = response.xpath('.//img[contains(@class,"media-img")]/@src').get()

        yield {"image": response.urljoin(image),"video":[]}
