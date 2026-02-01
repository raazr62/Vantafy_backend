import scrapy
import re

class CamclipsTvSpider(scrapy.Spider):
    name = "camclips.tv"
    emails = ["webcamdmca@protonmail.com", "abuse@ipvolume.net"]

    def clean(self, text):
        return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

    def __init__(self, name_query=None, *args, **kwargs):

        super(CamclipsTvSpider, self).__init__(*args, **kwargs)
        super().__init__(*args, **kwargs)

        self.name_query = name_query

        if not name_query:
            raise ValueError(
                "Provide a name_query. Example: -a name_query='Angela White'"
            )

        # Multiple names support
        if isinstance(name_query, str):
            names = [n.strip().lower().replace(" ", "-") for n in name_query.split(",")]
        elif isinstance(name_query, (list, tuple)):
            names = [str(n).strip().lower().replace(" ", "-") for n in name_query]
        else:
            raise ValueError("name_query must be a string or list")

        self.name_queries = names

    def start_requests(self):

        for name in self.name_queries:
            url = f"https://camclips.tv/search/{name}/"
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={"name_query": name},
            )

    def parse(self, response):
        # print(response.text)
        name_query = response.meta["name_query"]
        name = self.clean(name_query)
        # print(name)
        all_post = response.xpath('.//div[@class="list-videos"]//a')
        # print(all_post)
        for post in all_post:
            text = post.xpath(".//@title").get()
            text = self.clean(text)
            # print(text)
            if name in text:
                post_url = post.xpath(".//@href").get()
                # print(post_url)

                yield scrapy.Request(
                    url=post_url,
                    callback=self.parse_post,
                    meta={"name_query": name},
                )

        next_number = response.xpath(
            './/a[text()="Load more..."]/@data-parameters'
        ).get()

        name_slug = name_query.replace("-", "+")

        if next_number:
            m = re.search(r"from_videos\+from_albums:(\d+)", next_number)
            if m:
                match_number = int(m.group(1))
                next_url = f"https://camclips.tv/search/{name_query}/?mode=async&function=get_block&block_id=list_videos_videos_list_search_result&q={name_slug}&category_ids=&sort_by=&from_videos={match_number}"
                yield scrapy.Request(
                    next_url, callback=self.parse, meta={"name_query": name_query}
                )

    def parse_post(self, response):
        images = response.xpath('.//a[@rel="screenshots"]/@href').getall()
        yield {
            "page_url": response.url,
            "image": images
            }
