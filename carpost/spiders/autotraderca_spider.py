
from carpost.filters import CarpostFilter
from carpost.items import CarpostItem
from urllib.parse import urlencode
from scrapy import Selector
from furl import furl
import json
import scrapy
import logging
import datetime
import re
from fp.fp import FreeProxy
from pluck import pluck, ipluck

class AUTOTRADERCASpider(scrapy.Spider):
    name = 'AUTOTRADER_CA'
    page_num = 0
    perpage = 50
    url =  'https://www.autotrader.com/rest/searchresults/base?'
    detail_url = ''    
    header = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36'}
    # proxy = {'proxy': '209.212.33.99:8080'}
    proxy_ip = FreeProxy(timeout=1, rand=True, anonym=True).get()
    proxy = {'proxy': proxy_ip}
   
    def __init__(self, year=None, make=None, detail=None, *args, **kwargs):
        
        if year is not None:
            self.year = year
        else:
            self.year = datetime.datetime.now().year
        
        if make is not None:
            self.mkid = [make] 
        else:
            self.mkid = ['BMW','MB']

        if detail is not None:
            self.detail = detail
        else:
            self.detail = None
        super(AUTOTRADERCASpider, self).__init__(*args, **kwargs)

    def start_requests(self):
        if self.detail is not None:
             yield scrapy.http.Request(url=self.detail , headers=self.header , meta=self.proxy , callback=self.parse_item)
            #  yield scrapy.http.Request(url=self.detail , headers=self.header , callback=self.parse_item)
        else:
            params = {
                "fuelTypeGroup": 'GSL',
                "makeCodeList": ','.join(self.mkid),
                "sellerTypes": 'd',
                "listingTypes": 'CERTIFIED,USED',
                "searchRadius": 0,
                "zip": 97001,
                "startYear": self.year,
                "endYear": self.year,
                "marketExtension": 'include',
                "isNewSearch": 'false',
                "sortBy": 'yearDESC',
                "numRecords": self.perpage,
                "firstRecord": self.page_num
            }

            # 暫時只開網址建車功能
            # yield scrapy.http.Request(url=self.url + urlencode(params), headers=self.header, meta=self.proxy , callback=self.parse_page)

    def parse_page(self, response):
        if 'application/json' in str(response.headers['Content-Type']):
            res = json.loads(response.text)
            total_num = res.get('totalResultCount')
            # autotrader限制搜尋最大1000筆
            total_num = total_num if total_num < 1000 else 1001
            url = response.request.url
            new_url = furl(url)
            
            for num in range(self.page_num, total_num, self.perpage):
                new_url.args['firstRecord'] = num
                request_url = new_url.url
                yield scrapy.http.Request(url=request_url , headers=self.header, meta=self.proxy , callback=self.parse)
        else:
            logging.warn('not json type')

    def parse(self, response):
        if 'application/json' in str(response.headers['Content-Type']):
            res = json.loads(response.text)
            if res is not None:
                listinglist = res.get("listings")
                if len(listinglist) > 0:
                    detail_url = self.detail_url
                    for listingid in listinglist:
                        if len(listingid) > 0:
                            id = listingid['id']
                            yield scrapy.http.Request(url=detail_url % (id) , headers=self.header, meta=self.proxy , callback=self.parse_item)
                else:
                    logging.warn(listinglist)
            else:
                logging.warn(res)
        else:
            logging.warn('not json type')
            logging.warn(response.headers['Content-Type'])

    def parse_item(self, response):
        res = Selector(response)
        content_dom = res.xpath("//script[contains(text(),'deepLinkSavedSearch')]/text()").get()
        dom_text = re.findall(r"window\[\'ngVdpModel\'\]\s\=\s[{](.*?)[}][;]", content_dom)[0]
        dom_text = "{"+dom_text+"}"
        data = json.loads(dom_text)
    
        specs = data['specifications'].get('specs')
        bodystyle = ''
        engine = ''
        excolor = ''
        incolor = ''

        for item in specs:
            if item.get('key') == "Body Type":
                bodystyle = item.get('value')
            if item.get('key') == "Engine":
                engine = item.get('value')
            if item.get('key') == "Exterior Colour":
                excolor = item.get('value')
            if item.get('key') == "Interior Colour":
                incolor = item.get('value')

      
        items = CarpostItem()
        items['data_from']	        = 'AUTOTRADERCA'
        items['vin']	            = data['carInsurance'].get('vin')
        items['year']	            = data['hero'].get('year','')
        items['make']	            = data['hero'].get('make','')
        items['model']	            = data['hero'].get('model','')            
        items['trim']	            = data['hero'].get('trim', '')
        items['bodystyle']	        = bodystyle
        items['title']	            = data['deepLinkSavedSearch'].get('savedSearch').get('title')
        items['engine']	            = CarpostFilter.formatEngine(engine)
        items['price']	            = int(data['hero'].get('price').replace(',', ''))
        items['mileage']	        = CarpostFilter.formatKm(data['hero'].get('mileage')) * 0.62137
        items['location']	        = data['hero'].get('location')
        items['country']	        = 'CA'
        items['drivetrain']	        = data['highlights'].get('drivetrain')
        items['transmission']       = data['highlights'].get('transmission')
        items['highway_mpg']        = CarpostFilter.formatMpg(data['fuelEconomy'].get('fuelHighway'))
        items['city_mpg']	        = CarpostFilter.formatMpg(data['fuelEconomy'].get('fuelCity'))
        items['in_color']	        = incolor
        items['ex_color']	        = excolor
        items['url']	            = self.detail
        items['dealer']	            = data['ico'].get('dealerName')
        items['images']	            = pluck(data['gallery'].get('items'), 'photoViewerUrl')
        items['feature']	        = (data['featureHighlights'].get('highlights')+data['featureHighlights'].get('options'))

        # print('***************************** crawl content end *********************')
        yield items