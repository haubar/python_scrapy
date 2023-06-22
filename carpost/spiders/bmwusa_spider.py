from carpost.filters import CarpostFilter
from carpost.items import CarpostItem
from urllib.parse import urlencode
from scrapy import Selector
from furl import furl
import argparse
import scrapy
import json
import logging
import math



class BMWUSASpider(scrapy.Spider):
    name = 'BMWUSA'
    url = 'https://inventoryservices.bmwdealerprograms.com/vehicle'
    token = CarpostFilter.getBMWUSAtoken()
    header = {"Content-Type": "application/json","Authorization": "Bearer " + token}
    page_num = 0

    def __init__(self, year=None, detail=None, *args, **kwargs):
       
        if year is not None:
            self.year = [year]
        else:
            self.year = ['2016', '2017', '2018', '2019', '2020', '2021']
    
        if detail is not None:
            self.detail = detail
        else:
            self.detail = None

        super(BMWUSASpider, self).__init__(*args, **kwargs)
    
    def start_requests(self):
        if self.detail is not None:
            uri = furl(self.detail)
            vin = uri.fragment.path.segments[-1]
            data = {
                "VINs":[vin],
                "includeDealers": 1,
                "includeFacets": 0,
                "includeVehicles": 1,
                "postalCode": 91801,
            }
            body = json.dumps(data)
            yield scrapy.Request(url=self.url, callback=self.parse_detail, body=body, headers=self.header, method="POST")
        else:
            payload = {
                "PageSize": 100,
                "pageIndex": self.page_num,
                "postalCode": 91801,
                "Radius": 0,
                "SortBy": "",
                "SortDirection": "",
                "Filters": [
                            {'name':'CPOType','values':['All Pre-Owned']},
                            # {'name': 'CPOType', 'values': ["BMW Certified"]}	 拆分cpo及其它
                            {"name":"FuelType","values": ["Gasoline"]},
                            {'name':'Year','values':self.year}
                            # {'name':'Year','values':['2021']}
                        ]
                }
            body = json.dumps(payload)
            yield scrapy.Request(url=self.url, callback=self.parse_list, body=body, headers=self.header, method="POST")

    #列表總數抓取
    def parse_list(self, response):
        content = json.loads(response.text)
        count_total = content['totalRecords']
        page_size = content['pageSize']
        page_total = math.ceil(count_total/page_size)
        payload = json.loads(response.request.body)
    
        for num in range(self.page_num, count_total, page_size):
            payload['pageIndex'] = num
            body = json.dumps(payload)
            yield scrapy.Request(url=self.url, callback=self.parse_vehicle, body=body, headers=self.header, method="POST")
    
    #車輛完整資料
    def parse_vehicle(self, response):
        content = json.loads(response.text)
        inventories = content.get('vehicles')
        if len(inventories) > 0:
            vins = CarpostFilter.getVins(inventories ,'vin')
            data = {
                "VINs":vins
            }
            body = json.dumps(data)
            
            yield scrapy.Request(url=self.url, callback=self.parse_detail, body=body, headers=self.header, method="POST")

    def parse_detail(self, response):
        res = json.loads(response.text)
        dealers_info = res.get('dealers')[0]
        list_vehicles = res.get('vehicles')
        for data in list_vehicles:
            
            images = None
            if data.get('photos') is not None:
                images = ['https://bmw-inventory-assets-prod.azureedge.net/images/'+ s for s in data.get('photos')]
                
            #名稱處理
            title = str(data.get('year')) + ' ' + str(data.get('make')) + ' ' + str(data.get('modelDescription'))
            model = CarpostFilter.getModel(data.get('model'), data.get('modelDescription'))
            if data.get('trimDescription') is not None:
                title = str(data.get('year')) + ' ' + str(data.get('make')) + ' ' + str(data.get('trimDescription'))
                model = CarpostFilter.getModel(data.get('trim'), data.get('trimDescription'))
            if data.get('type') == 'CPO':	
                title = "Certified" + ' ' + title
            
            #配備處理
            features = ''
            if (data.get('allDescriptions') or data.get('optionDescriptions') ) is not None:
                features = (str(data.get('allDescriptions'))+'|'+str(data.get('optionDescriptions')) ).split('|')
            
            # 資料解析
            item = CarpostItem()
            item['data_from']   = 'BMWUSA'
            item['year']        = data.get('year')
            item['vin']         = data.get('vin')
            item['make']        = data.get('make')
            item['model']       = model
            item['trim']	    = data.get('trimDescription')
            item['bodystyle']   = data.get('bodyStyle')  
            item['title']       = title
            
            item['price']       = data.get('internetPrice')
            item['mileage']     = data.get('odometer')
            item['location']    = dealers_info.get('state')
            item['country']     = 'US'
            #直接定義美國來源
            
            item['highway_mpg'] = data.get('hwyMPG')
            item['city_mpg']    = data.get('cityMPG')
            item['drivetrain']  = data.get('drivetrain')
            item['transmission'] = data.get('transmissionType')
            item['cylinders'] = data.get('engineCylinders')
            
            item['dealer']      = dealers_info.get('dealerName')
            item['in_color']    = data.get('interiorMeta')
            item['ex_color']    = data.get('exteriorMeta')
            
            item['url']         = 'https://www.bmwusa.com/certified-preowned-search.html#/detail/' + data.get('vin')
            item['engine']      = CarpostFilter.formatEngine(CarpostFilter.getEngineDES(data.get('engineDisplacement'), data.get('engineDescription')))

            item['feature']     = features
            item['images']      = images
            yield item
