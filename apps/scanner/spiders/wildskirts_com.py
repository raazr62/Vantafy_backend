import scrapy
import unicodedata
import jmespath

class WildskirtsComSpider(scrapy.Spider):
    name = "wildskirts.com"
    emails = ["hello.wildskirts@gmail.com", "abuse@spaceship.com"]

    def match_name_words(self, name1, name2):
        def normalize(text):
            text = text.lower()
            text = "".join(
                c
                for c in unicodedata.normalize("NFD", text)
                if unicodedata.category(c) != "Mn"
            )
            return text

        n1 = normalize(name1).replace(" ", "")
        words2 = [normalize(w) for w in name2.split()]
        return all(w in n1 for w in words2) and sum(len(w) for w in words2) == len(n1)

    def __init__(self, name_query=None, *args, **kwargs):
        super(WildskirtsComSpider, self).__init__(*args, **kwargs)
        super().__init__(*args, **kwargs)

        if not name_query:
            raise ValueError(
                "Provide a name_query. Example: -a name_query='Angela White'"
            )
        self.name_query = name_query

        # Multiple names support
        if isinstance(name_query, str):
            names = [n.strip().lower().replace(" ", "+") for n in name_query.split(",")]
        elif isinstance(name_query, (list, tuple)):
            names = [str(n).strip().lower().replace(" ", "+") for n in name_query]
        else:
            raise ValueError("name_query must be a string or list")

        self.name_queries = names

    def start_requests(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0"
        }

        for name in self.name_queries:
            url = f"https://wildskirts.com/search?q={name}"
            yield scrapy.Request(
                url=url,
                headers=headers,
                callback=self.parse,
                meta={"page": 1, "name_query": name},
            )

    def parse(self, response):
        search_name = response.meta["name_query"].replace("+", " ")

        names = response.xpath('.//p[@class="font-semibold text-base"]/text()').getall()
        cl_name = [n.strip() for n in names if n.strip()]

        for idx, name in enumerate(cl_name):
            if self.match_name_words(search_name, name):
                profile_url = response.xpath(
                    f'(//div[@class="post"]/a)[{idx + 1}]/@href'
                ).get()
                if profile_url:
                    yield response.follow(
                        profile_url,
                        headers=response.request.headers,
                        callback=self.parse_profile,
                    )

    def parse_profile(self, response):
        api_id = response.xpath('.//button [@class="btn follow-btn"]/@data-celeb').get()
        if api_id:
            api_url = f"https://api.wildskirts.com/api/media/{api_id}"
            yield scrapy.Request(
                url=api_url,
                headers=response.request.headers,
                callback=self.parse_api,
            )

    def parse_api(self, response):
        json_data = response.json()
        print(json_data)

        data = jmespath.search("media.items", json_data)

        for idx in range(1, len(data) + 1):

            media_type = json_data.get("media").get("items").get(f"{idx}").get("t")
            media_url = json_data.get("media").get("items").get(f"{idx}").get("u")
            page_url = json_data.get("media").get("items").get(f"{idx}").get("l")
            # print("media_url:", media_url)

            if media_type == "photo":  # image
                yield {
                    "page_url": page_url,
                    "image": media_url
                }
            elif media_type == "video":
                thumbnail = json_data.get("media").get("items").get(f"{idx}").get("p")
                yield {
                    "page_url": page_url,
                    "image": thumbnail,
                    "video": media_url
                }
