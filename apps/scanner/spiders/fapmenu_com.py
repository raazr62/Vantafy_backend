import scrapy
import unicodedata
import json


class FapmenuComSpider(scrapy.Spider):
    name = "fapmenu.com"
    emails = ["abuse@server-panel.net", "admincrew@fapmenu.com"]

    def __init__(self, name_query=None, *args, **kwargs):
        self.url_list = []
        super(FapmenuComSpider, self).__init__(*args, **kwargs)

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
            c = c.replace("-", " ").replace("_", " ")
            c = " ".join(c.split()).lower()
            cleaned_list.append(c)

        self.name_queries = cleaned_list  # Make it a list always
        self.start_urls = ["https://fapmenu.com/search"]

    def start_requests(self):
        for q in self.name_queries:
            yield scrapy.FormRequest(
                url=self.start_urls[0],
                formdata={"searchVal": q},
                callback=self.parse,
                meta={"search_name": q},
            )

    def parse(self, response):
        search_name = response.meta["search_name"]

        profiles = response.xpath('.//a[@class="media-avatar-link"]')
        for profile in profiles:
            name = profile.xpath(".//text()").get()
            profile_url = profile.xpath(".//@href").get()

            if name:
                name = name.strip()

            if self.match_name_words(search_name, name):
                if profile_url:
                    yield response.follow(
                        profile_url,
                        callback=self.parse_profile,
                    )

    def parse_profile(self, response):
        image_url = response.xpath('.//div[@class="model-media-prew"]/a/@href').getall()
        for i in image_url:
            yield scrapy.Request(url=response.urljoin(i),callback=self.parse_image)

        next_page = response.xpath('.//a[text()="Next page"]/@href').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse_profile)

    def parse_image(self,response):
        image = response.xpath('.//img[contains(@class,"media-img")]/@src').get()
        yield{
            'image': response.urljoin(image),
            'video': []
        }

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
