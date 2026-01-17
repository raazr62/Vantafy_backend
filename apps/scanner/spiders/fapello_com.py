import scrapy
import unicodedata
import json


class FapelloComSpider(scrapy.Spider):
    name = "fapello.com"
    emails = ["johnfapello@gmail.com", "abuse@serverel.com"]
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
        super(FapelloComSpider, self).__init__(*args, **kwargs)

        if not name_query:
            raise ValueError(
                "Provide name_query. Examples:\n"
                "-a name_query='Mia Khalifa'\n"
                "-a name_query='Mia Khalifa, Ariana Grande'\n"
                '-a name_query=\'["Mia Khalifa","Ariana Grande"]\''
            )
        self.name_query = name_query

        # Try JSON list first
        try:
            parsed = json.loads(name_query)
            if isinstance(parsed, list):
                names = parsed
            else:
                names = [str(parsed)]
        except:
            # Otherwise treat as comma separated
            names = [n.strip() for n in name_query.split(",") if n.strip()]

        # Normalize all names → ALWAYS LIST
        cleaned_list = []
        for name in names:
            c = name.strip()
            c = c.lower()
            c = c.replace(" ", "-")

            cleaned_list.extend(
                [
                    f"https://fapello.com/search/{c}/",
                    # f"https://cz.fapello.com/search/{c}/",
                    # f"https://de.fapello.com/search/{c}/",
                    # f"https://es.fapello.com/search/{c}/",
                    # f"https://fr.fapello.com/search/{c}/",
                    # f"https://gr.fapello.com/search/{c}/",
                    # f"https://hu.fapello.com/search/{c}/",
                    # f"https://it.fapello.com/search/{c}/",
                    # f"https://jp.fapello.com/search/{c}/",
                    # f"https://nl.fapello.com/search/{c}/",
                    # f"https://pl.fapello.com/search/{c}/",
                    # f"https://pt.fapello.com/search/{c}/",
                    # f"https://ro.fapello.com/search/{c}/",
                    # f"https://ru.fapello.com/search/{c}/",
                    # f"https://se.fapello.com/search/{c}/",
                    # f"https://tr.fapello.com/search/{c}/",
                ]
            )

        self.start_urls = cleaned_list

    def start_requests(self):
        for url in self.start_urls:
            search_name = url.split("/")[-2].replace("-", " ")
            yield scrapy.FormRequest(
                url=url,
                callback=self.parse,
                dont_filter=True,
                meta={"search_name": search_name},
            )

    def parse(self, response):
        # .//div[contains(@class,"items-center absolute")]/a/@href
        search_name = response.meta["search_name"]
        # print(search_name)

        names = response.xpath(
            './/div[contains(@class,"items-center absolute")]/a//div[2]/text()'
        ).getall()
        cl_name = [n.strip() for n in names if n.strip()]

        for idx, name in enumerate(cl_name):
            if self.match_name_words(search_name, name):
                profile_url = response.xpath(
                    f'(//div[contains(@class,"items-center absolute")]/a)[{idx + 1}]/@href'
                ).get()
                if profile_url:
                    yield response.follow(
                        profile_url, callback=self.parse_profile, dont_filter=True
                    )

    def parse_profile(self, response):
        # print(response.url)
        redirect_flag = False
        if response.meta.get("redirect_urls"):
            redirect_flag = True

        self.url_list = []
        imgs = response.xpath('.//div[@id="content"]//img/@src').getall()

        for image_url in imgs:

            #     full = response.urljoin(image_url)
            #     if full not in self.url_list:
            #         self.url_list.append(full)
            if not redirect_flag:
                yield {"image": image_url, "video": []}

        next_page = response.xpath('.//div[@id="next_page"]/a/@href').get()

        if next_page:
            yield response.follow(next_page, callback=self.parse_profile)
