import scrapy
import base64

class ProxisSpider(scrapy.Spider):
    name = "advanced_name"
    start_urls = ["https://advanced.name/freeproxy?page=1"]
    api_urls = "https://test-rg8.ddns.net/api/post_proxies"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.count = 0
        self.limit = 150
        self.page = 1

    #Парсим данные с странице advanced_name
    def parse(self, response):
        for i, row in enumerate(response.css('tbody tr'), 1):
            if self.count >= self.limit: return
            self.count += 1
            yield {
                "ip" : base64.b64decode(row.css('td[data-ip]::attr(data-ip)').get()).decode('utf-8'),
                "port" : base64.b64decode(row.css('td[data-port]::attr(data-port)').get()).decode('utf-8'),
                "protocols": row.css('td:nth-child(4) a::text').getall()
            }
            
        # Для обработки страниц. Если не использовать, то паук будет брать данные только с первой страницы. Их примерно 100
        # По условию надо взять 150 прокси
        if self.count < self.limit:
            self.page += 1
            next_page = f"https://advanced.name/freeproxy/?page={self.page}"
            yield response.follow(next_page, callback = self.parse)

    #Загрузка данных на тестовое окружение
    def upload_to_form(self, request):
        i = 1
        yield {
            f"save_id_{i}" : ["n15"]
        }
#t_1363631d