# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals


import requests
import os

# 亂寫寫三小
class CarpostSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(s.spider_closed, signal=signals.spider_closed)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('抓取 開始: %s' % spider.name)
        url = 'https://carpost.requestcatcher.com/test?cp2='
        yield scrapy.http.Request(url=url)
        requests.get(url)

    def spider_closed(self, spider):
        spider.logger.info('抓取 結束: %s' % spider.name)
        requests.get('http://cp2.carpost.tw/api/getScrapinghub?id=' + os.environ['SCRAPY_JOB'])


class CarpostRefactorMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(s.spider_closed, signal=signals.spider_closed)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('抓取 開始: %s' % spider.name)
        requests.get('https://carpost.requestcatcher.com/test?spider=' + spider.name) 

    def spider_closed(self, spider):
        spider.logger.info('抓取 結束: %s' % spider.name)
        spider.logger.info('抓取 結束 job id: %s' % os.environ['SCRAPY_JOB'])
        requests.get('https://carpost.requestcatcher.com/test?job=' + os.environ['SCRAPY_JOB'])
        # requests.get('https://cbeta.carpost.tw/api/getscraphubsource?jobid=' + os.environ['SCRAPY_JOB'])
        requests.post('https://cbeta.carpost.tw/api/getscraphubsource?jobid=' + os.environ['SCRAPY_JOB'])