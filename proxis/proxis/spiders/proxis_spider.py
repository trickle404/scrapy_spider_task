import scrapy
import base64

class ProxisSpider(scrapy.Spider):
    name = "advanced_name"
    start_urls = ["https://advanced.name/freeproxy?page=1"]

    custom_settings = {
        'CLOSESPIDER_ITEMCOUNT':150,
        'CONCURRENT_REQUESTS':1,
        'DOWNLOAD_DELAY':1
    }

    def parse(self, response):
        for i, row in enumerate(response.css('tbody tr'), 1):
            if i > 150: break
            yield {
                "ip" : base64.b64decode(row.css('td[data-ip]::attr(data-ip)').get()).decode('utf-8'),
                "port" : base64.b64decode(row.css('td[data-port]::attr(data-port)').get()).decode('utf-8'),
                "protocols": row.css('td:nth-child(4) a::text').getall()
            }
#t_1363631d