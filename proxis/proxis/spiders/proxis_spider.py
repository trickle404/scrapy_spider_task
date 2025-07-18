import scrapy
import base64

class ProxisSpider(scrapy.Spider):
    name = "advanced_name"
    start_urls = ["https://advanced.name/freeproxy?page=1"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.count = 0
        self.limit = 150
        self.page = 1

    def parse(self, response):
        for i, row in enumerate(response.css('tbody tr'), 1):
            if self.count > self.limit: return
            self.count += 1
            yield {
                "ip" : base64.b64decode(row.css('td[data-ip]::attr(data-ip)').get()).decode('utf-8'),
                "port" : base64.b64decode(row.css('td[data-port]::attr(data-port)').get()).decode('utf-8'),
                "protocols": row.css('td:nth-child(4) a::text').getall()
            }
            

        if self.count <= self.limit:
            self.page += 1
            next_page = f"https://advanced.name/freeproxy/?page={self.page}"
            yield response.follow(next_page, callback = self.parse)
#t_1363631d