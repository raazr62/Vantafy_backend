import scrapy
import re
from urllib.parse import urlparse
import json


class XxbritsComSpider(scrapy.Spider):
    name = "xxbrits.com"
    emails = ["xxbrits@protonmail.com", "abuse@medera.cloud"]

    def __init__(self, name_query=None, *args, **kwargs):
        super(XxbritsComSpider, self).__init__(*args, **kwargs)
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
            url = f"https://www.xxbrits.com/search/{name}-db3e6e/"
            yield scrapy.Request(
                url=url,
                headers=headers,
                callback=self.parse,
                meta={"name_query": name},
            )

    def clean(self, text):
        # lowercase + keep only letters & numbers
        return re.sub(r"[^a-z0-9]+", "", text.lower())

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
        post_links = response.xpath('.//a[@class="card-image"]/@href').getall()
        # Follow post pages
        for post in post_links:
            yield scrapy.Request(
                url=response.urljoin(post),
                headers=response.request.headers,
                callback=self.parse_post,
                meta={"name_query": name_slug},
            )

        # Albums page link
        albums_url = response.xpath(
            f'.//a[@class="media"][@title="{name_title}"]/@href'
        ).getall()

        # Stop pagination if no more results
        if albums_url:
            for i in albums_url:
                yield scrapy.Request(
                    url=response.urljoin(i),
                    headers=response.request.headers,
                    callback=self.parse_albums,
                )

        name_q = name_slug.replace("-", "+")
        next_number = response.xpath(
            '(.//div[@class="item pager next_page"]/a/@data-parameters)[position()=1]'
        ).get()

        if next_number:
            m = re.search(r"from_videos\+from_albums:(\d+)", next_number)
            if m:
                match_number = int(m.group(1))
                next_url = f"https://www.xxbrits.com/search/{name_slug}-154773/?mode=async&function=get_block&block_id=list_videos_videos_list_search_result&q={name_q}&category_ids=&sort_by=&from_videos={match_number}"
                yield scrapy.Request(
                    next_url, callback=self.parse, meta={"name_query": name_slug}
                )

        next_album = response.xpath(
            '(.//div[@class="item pager next_page"]/a/@data-parameters)[position()=2]'
        ).get()
        if next_album:
            match = re.search(r"from_videos\+from_albums:(\d+)", next_album)
            if match:
                match_number_album = int(match.group(1))
                next_url = f"https://www.xxbrits.com/search/{name_slug}-154773/?mode=async&function=get_block&block_id=list_albums_albums_list_search_result&q={name_q}&category_ids=&sort_by=&from_albums={match_number_album}"
                yield scrapy.Request(
                    next_url, callback=self.parse, meta={"name_query": name_slug}
                )

    def parse_post(self, response):
        name_query = response.meta.get("name_query")

        tegs = response.xpath('.//div[@class="tags-list"]/a/text()').getall()
        video_text = response.xpath('.//div[@class="headline"]/h1/text()').get()
        tegs = " ".join(tegs)

        if self.clean(name_query) in self.clean(video_text) or self.clean(
            name_query
        ) in self.clean(tegs):
            json_text = response.xpath(
                'normalize-space((.//script[@type="application/ld+json"])[last()]/text())'
            ).get()

            if json_text:
                data = json.loads(json_text)
                graph = data.get("@graph", [])
                node = graph[0]
                video = node.get("contentUrl")
                image = node.get("thumbnailUrl")
                yield {
                    "page_url": response.url,
                    "image": image,
                    "video": video
                }

    def parse_albums(self, response):
        img_urls = response.xpath(
            './/a[@class="item-album item link-post"]/@href'
        ).getall()

        yield {
            "page_url": response.url,
            "image": img_urls
        }
