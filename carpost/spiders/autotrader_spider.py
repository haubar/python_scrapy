
from carpost.filters import CarpostFilter
from carpost.items import CarpostItem
from urllib.parse import urlencode
from scrapy import Selector
from furl import furl
import json
import scrapy
import logging
import math
import datetime
from fp.fp import FreeProxy
from pluck import pluck, ipluck

class AUTOTRADERSpider(scrapy.Spider):
    name = 'AUTOTRADER'
    page_num = 0
    perpage = 50
    url =  'https://www.autotrader.com/rest/searchresults/base?'
    detail_url = 'https://www.autotrader.com/cars-for-sale/vehicledetails.xhtml?clickType=listing&listingId=%s'    
    header = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36'}
    # proxy = {'proxy': '209.212.33.99:8080'}
    proxy_ip = FreeProxy(timeout=1, rand=True, anonym=True).get()
    proxy = {'proxy': proxy_ip}
    print(proxy)
    print(proxy)
    def __init__(self, year=None, make=None, detail=None, *args, **kwargs):
        # proxy = FreeProxy(country_id=['US'], timeout=0.3, rand=True).get()

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
        super(AUTOTRADERSpider, self).__init__(*args, **kwargs)

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

        
            yield scrapy.http.Request(url=self.url + urlencode(params), headers=self.header, meta=self.proxy , callback=self.parse_page)

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
        content_data = res.xpath('//script[contains(..,"window.__BONNET_DATA__")]//text()').get().replace('window.__BONNET_DATA__=','')
        data = json.loads(content_data)

        vehicle_data = data.get('initialState').get('birf').get('pageData').get('page').get('vehicle')
        car_id      = vehicle_data.get('car_id')
        inventory_data = data.get('initialState').get('inventory').get(str(car_id))
        owner_id    = inventory_data.get('owner')
        owner_data  = data.get('initialState').get('owners').get(str(owner_id))
        all_image = pluck(inventory_data.get('images').get('sources'), 'src')
      
        items = CarpostItem()
        items['data_from']	        = 'AUTOTRADER'
        items['vin']	            = vehicle_data.get('vin','')
        items['year']	            = inventory_data.get('year','')
        items['make']	            = inventory_data.get('make','')
        items['model']	            = inventory_data.get('model','')            
        items['trim']	            = inventory_data.get('trim')
        items['bodystyle']	        = vehicle_data.get('body_code')[0]
        items['title']	            = inventory_data.get('listingTitle')
        items['engine']	            = CarpostFilter.formatEngine(inventory_data.get('specifications').get('engineDescription').get('value',''))
        items['price']	            = vehicle_data.get('price')
        items['mileage']	        = CarpostFilter.formatMile(inventory_data.get('specifications').get('mileage').get('value'))
        items['location']	        = owner_data.get('location').get('address').get('state')
        items['country']	        = 'US'
        items['drivetrain']	        = inventory_data.get('specifications').get('driveType').get('value','')
        items['transmission']       = inventory_data.get('specifications').get('transmission').get('value','')
        items['highway_mpg']        = inventory_data.get('mpgHighway')
        items['city_mpg']	        = inventory_data.get('mpgCity')
        items['in_color']	        = inventory_data.get('specifications').get('interiorSeats').get('value','')
        items['ex_color']	        = inventory_data.get('specifications').get('exterior').get('value','')
        items['url']	            = self.detail_url % (car_id)
        items['dealer']	            = owner_data.get('name')
        items['images']	            = all_image
        items['feature']	        = inventory_data.get('additionalInfo').get('vehicleFeatures')

        # print('***************************** crawl content end *********************')
        yield items