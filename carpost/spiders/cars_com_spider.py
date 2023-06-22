from carpost.filters import CarpostFilter
from carpost.items import CarpostItem
from urllib.parse import urlencode
from scrapy import Selector
from furl import furl
import datetime
import scrapy
import re
import json
import logging
import math

class CARSSpider(scrapy.Spider):
    name = 'CARS_ALL'
    page_num = 1
    header = {'User-Agent':'Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'}
    # url =  'https://www.cars.com/for-sale/listings/?'
    url = 'https://www.cars.com/shopping/results/?'
    # detail_url = 'https://www.cars.com/vehicledetail/detail/%s/overview/'
    detail_url ='https://www.cars.com/vehicledetail/'
    def __init__(self, year=None, make=None, detail=None, *args, **kwargs):
        if year is not None:
            self.year = year
        else:
            self.year = '2016'
        
        if make is not None:
            self.make = make 
        else:
            self.make = 'alfa_romeo,bmw,mercedes_benz,porsche,ford,dodge,chevrolet,honda,toyota,bentley,rolls_royce,maserati'

        if detail is not None:
            self.detail = detail
        else:
            self.detail = None

        super(CARSSpider, self).__init__(*args, **kwargs)


    def start_requests(self):
        
        if self.detail is not None:
            yield scrapy.http.Request(url=self.detail , callback=self.parse_item)

        else:
            params = {
                'dealer_id': '',
                'fuel_slugs[]': 'gasoline',
                'stock_type': 'used',
                'list_price_max': '',
                'list_price_min': 20000,
                'makes[]': self.make.split(',') ,
                'maximum_distance': '',
                'mileage_max': 62000,
                'page_size': 100,
                'page': self.page_num,
                'sort': 'listed_at_desc',
                'year_min': self.year,
                'year_max': datetime.datetime.now().year,
                'zip': 97001
            }
            yield scrapy.http.Request(url=self.url+urlencode(params, True), callback=self.parse_page)

    # 分頁索引
    def parse_page(self, response):
        res = Selector(response=response)
        # list_dom = res.xpath('//div[contains(@class, "listings-page")]')
        list_data = res.xpath('//*[@id="search-live-content"]').xpath('@data-site-activity').get()
        if list_data is not None:
            data = json.loads(list_data)
            total_page = data['result_page_count']
            url = response.request.url
            new_url = furl(url)
          
            total_page = total_page if total_page <= 50 else 51
            for num in range(total_page):
                new_url.args['page'] = num+1
                request_url = new_url.url
                yield scrapy.http.Request(url=request_url, callback=self.parse)


    # 列表資料
    def parse(self, response):
                res = Selector(response=response)
                list_data = res.xpath('//*[@id="search-live-content"]').xpath('@data-site-activity').get()
                if list_data is not None:
                    data = json.loads(list_data)
                    listing_ids = data['listing_ids']
                    if len(listing_ids) > 0:
                        detail_url = self.detail_url
                        header = self.header
                        for page_id in listing_ids:
                            # logging.warn('page id %s' % (page_id))
                            yield scrapy.http.Request(url=detail_url+page_id, headers=header, callback=self.parse_item)
                    else:
                        logging.warn('no get detail id')                
                else:
                    logging.warn('no data')
           
              
    

    # 解析內容
    def parse_item(self, response):
                res = Selector(response=response)
                title = res.xpath('//h1[@class="listing-title"]/text()').get()
                seller_name = res.xpath('//h3[contains(@class, "seller-name")]/text()').get()
                engine_dom = res.xpath('//dl[@class="fancy-description-list"]').get()
                engine = re.findall("\d+\.\d+L", engine_dom)[0].replace('L', '')
                # cylinder = re.findall("[-]?+\d+", engine_dom)
                cylinder = 0
                mpgdom = res.xpath('//span[@class="js-tooltip-container"]/span[@class="sds-tooltip"]/span/text()').get()
                if mpgdom is not None:
                    mpg = mpgdom.split('–')
                    city_mpg = mpg[0]
                    highway_mpg = mpg[1]
                

                allphoto = res.xpath('//img[contains(@class, "swipe-main-image")]/@data-src').extract()
                if len(allphoto) == 0:
                    allphoto = res.xpath('//img[contains(@class, "swipe-main-image")]/@src').extract()


                content_dom = res.xpath("//script[contains(text(),'CarsWeb.ListingController.show')]/text()").get()
                dom_text = re.findall(r'[(][{](.*?)[}][)]', content_dom)[-1]
                dom_text = "{"+dom_text+"}"    
                content_data = json.loads(dom_text).get('CarsWeb.ListingController.show').get('callSourceDniMetadata')

                base_data = content_data.get('dimensions')
                state = content_data.get('user').get('state')
               
                items = CarpostItem()
                items['data_from']	    = 'CARS'
                items['vin']	        = base_data.get('vin')
                items['year']	        = base_data.get('year')
                items['make']	        = base_data.get('make')[0]
                items['model']	        = base_data.get('model')[0]
                items['trim']	        = "".join(base_data.get('trim'))
                items['bodystyle']	    = "".join(base_data.get('bodyStyle'))
                items['title']	        = title
                items['price']	        = base_data.get('price')
                items['mileage']	    = base_data.get('mileage')
                items['location']	    = state
                items['country']	    = "US" #只有美國
                items['drivetrain']	    = "".join(base_data.get('drvTrnId'))
                items['transmission']   = "".join(base_data.get('transTypeId'))
                items['in_color']	    = "".join(base_data.get('intColor'))
                items['ex_color']	    = "".join(base_data.get('extColor'))
                items['url']	        = response.url 
                items['dealer']	        = seller_name
                items['highway_mpg']    = highway_mpg
                items['city_mpg']	    = city_mpg
                items['engine']	        = engine
                items['cylinders']      = cylinder
                
                items['images']	        = allphoto
                # items['feature']	    = ";".join(base_data.get('normFeatureId'))
                items['feature']	    = base_data.get('normFeatureId')
                
                yield items

