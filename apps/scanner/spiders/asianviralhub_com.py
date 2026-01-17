import scrapy
import re
from urllib.parse import urlparse
import json


class AsianviralhubComSpider(scrapy.Spider):
    name = "asianviralhub.com"
    emails = ["ABUSE@mojohost.com"]

    def __init__(self, name_query=None, *args, **kwargs):
        super(AsianviralhubComSpider, self).__init__(*args, **kwargs)
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
            url = f"https://asianviralhub.com/search/{name}/"
            yield scrapy.Request(
                url=url,
                headers=headers,
                callback=self.parse,
                meta={"page": 1, "name_query": name},
            )

    def parse(self, response):

        name_slug = response.meta["name_query"]

        # Extract readable name
        match = re.search(r"/search/([^/]+)/?", urlparse(response.url).path)
        if match:
            slug = match.group(1)
            clean_name = re.sub(r"-[a-fA-F0-9]{5,}$", "", slug)
            name_title = clean_name.replace("-", " ").title()
        else:
            name_title = "Unknown"

        # Extract posts
        post_links = response.xpath(
            f'.//a[contains(@title,"{name_title}")]/@href'
        ).getall()

        # Albums page link
        albums_url = response.xpath(
            f'.//div[@class="list-albums"]//a[@title="{name_title}"]/@href'
        ).get()

        # Follow post pages
        for post in post_links:
            yield scrapy.Request(
                url=response.urljoin(post),
                headers=response.request.headers,
                callback=self.parse_post,
                meta={"albums_url": albums_url},
            )

        # Stop pagination if no more results
        if not post_links:
            if albums_url:
                yield scrapy.Request(
                    url=response.urljoin(albums_url),
                    headers=response.request.headers,
                    callback=self.parse_albums,
                )

        name_q = name_slug.replace("-", "+")

        next_number = response.xpath(
            '(.//li[@class="next"]/a/@data-parameters)[position()=1]'
        ).get()
        if next_number:
            m = re.search(r"from_videos\+from_albums:(\d+)", next_number)
            if m:
                match_number = int(m.group(1))
                next_url = f"https://asianviralhub.com/search/{name_slug}/?mode=async&function=get_block&block_id=list_videos_videos_list_search_result&q={name_q}&category_ids=&sort_by=&from_videos={match_number}"
                yield scrapy.Request(
                    next_url, callback=self.parse, meta={"name_query": name_slug}
                )
        # Pagination #2 (albums)
        next_album = response.xpath(
            '(.//li[@class="next"]/a/@data-parameters)[position()=2]'
        ).get()
        if next_album:
            match = re.search(r"from_videos\+from_albums:(\d+)", next_album)
            if match:
                match_number_album = int(match.group(1))
                next_url = f"https://asianviralhub.com/search/{name_slug}/?mode=async&function=get_block&block_id=list_albums_albums_list_search_result&q={name_q}&category_ids=&sort_by=&from_albums={match_number_album}"
                yield scrapy.Request(
                    next_url, callback=self.parse, meta={"name_query": name_slug}
                )

    def parse_post(self, response):
        json_text = response.xpath(
            'normalize-space(.//script[@type="application/ld+json"]/text())'
        ).get()

        if json_text:
            data = json.loads(json_text)

            video = data.get("contentUrl")
            image = response.xpath('.//div[@class="block-screenshots"]/a/@href').getall()

            yield {
                "image": image,
                "video": video
            }

    def parse_albums(self, response):
        img_urls = response.xpath('.//div[@class="images"]/a/@href').getall()

        yield {"image": img_urls, "video": response.url}
