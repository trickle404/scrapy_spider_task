import scrapy
import base64
import json
import time

from scrapy.http import JsonRequest
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import TimeoutError, DNSLookupError
from twisted.web._newclient import ResponseFailed

class ProxisSpider(scrapy.Spider):
    name = "advanced_name"
    start_urls = ["https://advanced.name/freeproxy?page=1"]
    custom_settings = {
        'DOWNLOAD_DELAY': 5,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'CONCURRENT_REQUESTS': 1,
        'RETRY_TIMES': 5,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429],
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 10,
        'AUTOTHROTTLE_MAX_DELAY': 300,
        'ROBOTSTXT_OBEY': True,
        'HTTPERROR_ALLOWED_CODES': [429],
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_urls = "https://test-rg8.ddns.net/task"
        self.count = 0
        self.limit = 150
        self.page = 1
        self.list_proxis = []
        self.user_id = "t_1363631d"
        self.batch_index = 0
        self.batch_size = 10
        self.results = {}
        self.start_time = time.time()

    def parse(self, response):
        for row in response.css('tbody tr'):
            if self.count >= self.limit:
                break
            proxy_data = {
                "ip": base64.b64decode(row.css('td[data-ip]::attr(data-ip)').get()).decode('utf-8'),
                "port": base64.b64decode(row.css('td[data-port]::attr(data-port)').get()).decode('utf-8'),
                "protocols": row.css('td:nth-child(4) a::text').getall()
            }
            self.list_proxis.append(proxy_data)
            self.count += 1
            yield proxy_data

        if self.count < self.limit:
            self.page += 1
            next_page = f"https://advanced.name/freeproxy/?page={self.page}"
            yield response.follow(next_page, callback=self.parse)
        else:
            yield scrapy.Request(
                url=self.api_urls,
                callback=self.send_proxies,
                meta={'cookiejar': 1},
                dont_filter=True
            )

    def send_proxies(self, response):
        if response.status == 429:
            self.logger.error("429 Too Many Requests on /task")
            time.sleep(30)
            return scrapy.Request(
                url=self.api_urls,
                callback=self.send_proxies,
                meta={'cookiejar': 1},
                dont_filter=True
            )

        start = self.batch_index * self.batch_size
        end = start + self.batch_size
        batch = self.list_proxis[start:end]

        if not batch:
            self.logger.info("All batches sent.")
            return

        return scrapy.Request(
            url="https://test-rg8.ddns.net/api/get_token",
            callback=self.post_proxies,
            meta={
                'cookiejar': 1,
                'batch': batch,
                'batch_index': self.batch_index
            },
            dont_filter=True
        )

    def post_proxies(self, response):
        if response.status == 429:
            self.logger.warning("429 on get_token, retrying /task in 30s")
            time.sleep(30)
            return scrapy.Request(
                url=self.api_urls,
                callback=self.send_proxies,
                meta={'cookiejar': 1},
                dont_filter=True
            )

        batch = response.meta['batch']
        batch_index = response.meta['batch_index']

        payload = {
            "user_id": self.user_id,
            "len": len(batch),
            "proxies": ", ".join([f"{p['ip']}:{p['port']}" for p in batch])
        }

        return JsonRequest(
            url="https://test-rg8.ddns.net/api/post_proxies",
            data=payload,
            callback=self.handle_response,
            errback=self.handle_error,
            meta={
                'cookiejar': 1,
                'batch': batch,
                'batch_index': batch_index
            },
            dont_filter=True
        )

    def handle_response(self, response):
        if response.status == 429:
            self.logger.warning("429 on post_proxies, retrying /task in 30s")
            time.sleep(30)
            return scrapy.Request(
                url=self.api_urls,
                callback=self.send_proxies,
                meta={'cookiejar': 1},
                dont_filter=True
            )

        try:
            data = response.json()
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON response: {response.text}")
            return

        save_id = data.get("save_id") or f"batch_{response.meta['batch_index']}"
        batch = response.meta["batch"]
        self.results[save_id] = [f"{p['ip']}:{p['port']}" for p in batch]
        self.logger.info(f"Batch {response.meta['batch_index']} saved with id: {save_id}")

        self.batch_index += 1
        yield scrapy.Request(
            url=self.api_urls,
            callback=self.send_proxies,
            meta={'cookiejar': 1},
            dont_filter=True
        )

    def handle_error(self, failure):
        self.logger.error(f"[Failure] {type(failure)}")
        if failure.check(HttpError):
            response = failure.value.response
            self.logger.error(f"HttpError {response.status}: {response.url}")
        elif failure.check(TimeoutError, DNSLookupError, ResponseFailed):
            self.logger.error(f"Connection error: {failure.getErrorMessage()}")
        else:
            self.logger.error(f"Unknown error: {failure}")

    def closed(self, reason):
        elapsed = time.time() - self.start_time
        hours, rem = divmod(int(elapsed), 3600)
        minutes, seconds = divmod(rem, 60)
        final_time = f"{hours:02}:{minutes:02}:{seconds:02}"

        with open("results.json", "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=4)

        with open("time.txt", "w", encoding="utf-8") as f:
            f.write(final_time)

        self.logger.info(f"Spider closed: total time = {final_time}")
