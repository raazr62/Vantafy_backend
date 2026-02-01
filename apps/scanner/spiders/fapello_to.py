import scrapy
import unicodedata
import json

class FapelloToSpider(scrapy.Spider):
    # fappello.is is also same and the url of image is also same
    name = "fapello.to"
    emails = [
        "abuse@as201744.net",
        "9b3e8f363f874375ad6c4b7befa5310e.protect@withheldforprivacy.com",
    ]
    # fapello.is is also same because both use same API.
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
        self.url_list = []
        self.stop_flag = False
        super(FapelloToSpider, self).__init__(*args, **kwargs)

        if not name_query:
            raise ValueError(
                "Provide name_query. Examples:\n"
                "-a name_query='Mia Khalifa'\n"
                "-a name_query='Mia Khalifa, Ariana Grande'\n"
                '-a name_query=\'["Mia Khalifa","Ariana Grande"]\''
            )
        self.name_query = name_query
        try:
            parsed = json.loads(name_query)
            if isinstance(parsed, list):
                names = parsed
            else:
                names = [str(parsed)]
        except:
            names = [n.strip() for n in name_query.split(",") if n.strip()]

        # Normalize all names → ALWAYS LIST
        self.cleaned_list = []
        for name in names:
            c = name.strip()
            c = c.lower()
            c = c.replace(" ", "%20")

            self.cleaned_list.append(c)

        self.start_urls = ["https://fapello.to/"]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={"search_name": self.cleaned_list},
            )

    def parse(self, response):
        url = f"{response.url}/search"
        yield response.follow(
            url=url,
            callback=self.parse_search,
            meta={"search_name": response.meta["search_name"]},
        )

    def parse_search(self, response):

        search_name = response.meta["search_name"]

        for name in search_name:
            url = f"{response.url}/{name}/"

            yield response.follow(
                url=url,
                callback=self.parse_search_results,
                meta={"search_name": name},
            )

    def parse_search_results(self, response):

        search_name = response.meta["search_name"]
        orginal_name = search_name.replace("%20", " ")

        names = response.xpath(
            './/div[contains(@class,"girlfound")]//span/a/text()'
        ).getall()

        cl_name = [n.strip() for n in names if n.strip()]

        for idx, name in enumerate(cl_name):
            if self.match_name_words(orginal_name, name):
                profile_url = response.xpath(
                    f'(//div[contains(@class,"girlfound")]//span/a)[{idx + 1}]/@href'
                ).get()
                if profile_url:
                    yield response.follow(profile_url, callback=self.parse_profile)

    def parse_profile(self, response):
        model_id = response.url.split("/")[-1]
        headers = {
            "Referer": response.url,
            "sec-ch-ua": '"Chromium";v="142", "Microsoft Edge";v="142", "Not_A Brand";v="99"',
        }

        page = 1
        api_url = [
            f"https://fapello.to/api/media/{model_id}/{page}/1/1",
            f"https://fapello.to/api/media/{model_id}/{page}/1/2",
        ]

        for url in api_url:
            yield scrapy.Request(
                url=url,
                headers=headers,
                callback=self.parse_media,
                meta={"model_id": model_id, "page": page, "headers": headers},
                dont_filter=True,
            )

    def parse_media(self, response):
        model_id = response.meta["model_id"]
        page = response.meta["page"]
        headers = response.meta["headers"]

        try:
            data = response.json()
        except:
            return

        if not data:
            return

        # Extract media
        for item in data:
            media_type = item.get("type")
            media_url = item.get("newUrl")
            video_img_url = item.get("newUrlThumb")
            page_id = item.get("id")
            page_url = f"https://fapello.to/post/{page_id}"

            if media_type == "1":  # image
                yield {
                    "page_url": page_url, 
                    "image": media_url or video_img_url
                }
            elif media_type == "2":  # video
                yield {
                    "page_url": page_url,
                    "image": video_img_url,
                    "video": media_url
                }

        # Request next page
        next_page = page + 1
        next_api_url = [
            f"https://fapello.to/api/media/{model_id}/{next_page}/1/1",
            f"https://fapello.to/api/media/{model_id}/{next_page}/1/2",
        ]

        for next_url in next_api_url:
            yield scrapy.Request(
                url=next_url,
                headers=headers,
                callback=self.parse_media,
                meta={"model_id": model_id, "page": next_page, "headers": headers},
                dont_filter=True,
            )
