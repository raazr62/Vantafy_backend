import scrapy
import re
import json

class NoodlemagazineComSpider(scrapy.Spider):
    name = "noodlemagazine.com"
    emails = ["abuse@noodlemagazine.com", "abuse@pvvstream.pro"]
    custom_settings = {
        "DOWNLOAD_DELAY": 1,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "CONCURRENT_REQUESTS": 4,
        "RETRY_TIMES": 1,
        "DOWNLOAD_TIMEOUT": 20,
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0",
    }

    def __init__(self, name_query=None, *args, **kwargs):
        super(NoodlemagazineComSpider, self).__init__(*args, **kwargs)
        super().__init__(*args, **kwargs)

        if not name_query:
            raise ValueError(
                "Provide a name_query. Example: -a name_query='Angela White'"
            )
        self.name_query = name_query

        # Multiple names support
        if isinstance(name_query, str):
            names = [
                n.strip().lower().replace(" ", "%20") for n in name_query.split(",")
            ]
        elif isinstance(name_query, (list, tuple)):
            names = [str(n).strip().lower().replace(" ", "%20") for n in name_query]
        else:
            raise ValueError("name_query must be a string or list")

        self.name_queries = names

    def start_requests(self):
        headers = {
            "sec-ch-ua-platform": '"Windows"',
            "Referer": "https://noodlemagazine.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0",
            "sec-ch-ua": '"Chromium";v="142", "Microsoft Edge";v="142", "Not_A Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
        }

        for name in self.name_queries:
            url = f"https://noodlemagazine.com/video/{name}/"
            yield scrapy.Request(
                url=url,
                headers=headers,
                callback=self.parse,
                meta={"page": 1, "name_query": name},
            )

    def parse(self, response):
        stop_indicator = response.xpath('.//div[@class="alert_warning"]/text()').get()
        if stop_indicator:
            return
        name_query = response.meta.get("name_query")
        name = name_query.replace("%20", " ").lower()

        page = response.meta.get("page", 1)
        post_links = response.xpath(
            f".//img[contains(translate(@alt, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{name}')]/parent::div/parent::a/@href"
        ).getall()
        for post in post_links:
            yield scrapy.Request(
                url=response.urljoin(post),
                headers=response.request.headers,
                callback=self.parse_post,
            )

        next_page_url = f"https://noodlemagazine.com/video/{name_query}?p={page}"
        yield scrapy.Request(
            url=next_page_url,
            headers=response.request.headers,
            callback=self.parse,
            # dont_filter=True,
            meta={"page": page + 1, "name_query": name_query},
        )

    def parse_post(self, response):
        script_text = response.xpath(
            './/script[contains(text(),"window.playlist")]/text()'
        ).get()

        # 1. Extract the {...} part of window.playlist
        m = re.search(r"window\.playlist\s*=\s*(\{.*?\});", script_text, re.DOTALL)
        playlist_js = m.group(1)

        # 2. Convert JS booleans to JSON booleans
        playlist_json = playlist_js.replace("true", "true").replace("false", "false")

        # 3. Load JSON
        data = json.loads(playlist_json)

        image = data.get("image")
        yield {
            "image": image,
            "video": data.get("sources")[0].get("file") if data.get("sources") else None
        }
