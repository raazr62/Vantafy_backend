import scrapy
import re

class NudostarComSpider(scrapy.Spider):
    name = "nudostar.com"
    emails = ["abuse@internet.bs", "OWNER@nudostar.com.customers.whoisprivacycorp.com"]
    def __init__(self, name_query=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not name_query:
            raise ValueError("Usage: scrapy crawl nudo -a name_query='Mia Khalifa'")

        # Normalize query
        self.name_query = name_query
        self.name_query_lower = self.name_query.lower()

        # Build search URL: lowercase + replace spaces with dashes
        search_query = self.name_query_lower.replace(" ", "-")
        self.start_urls = [f"https://nudostar.com/search/{search_query}/"]

    def clean(self,text):
        # lowercase + keep only letters & numbers
        return re.sub(r"[^a-z0-9]+", "", text.lower())

    def parse(self, response):
        # Extract all profile links and names from search page
        profiles = response.xpath('//h2[@class="entry-title heading-size-1"]/a')

        for profile in profiles:
            # Name can be inside <b> or direct text
            name = profile.xpath(".//b/text() | ./text()").get(default="").strip()
            profile_url = profile.xpath("./@href").get()

            # Match case-insensitive
            if self.clean(name) in self.clean(self.name_query):
                yield scrapy.Request(
                    url=profile_url,
                    callback=self.parse_profile,
                    meta={"name": name, "profile_url": profile_url},
                )

    def parse_profile(self, response):
        data = response.xpath('.//div[@class="item_content"]')
        for i in data:
            image_url = i.xpath('.//div[@class="item_img"]/img/@src').get()
            page_url = i.xpath('.//a/@href').get()
        
            yield {
                "page_url": page_url,
                "image": image_url
            }

        next_url = response.xpath('.//a[@class="next-post"]/@href').get()
        if next_url:
            yield scrapy.Request(next_url, callback=self.parse_profile)
