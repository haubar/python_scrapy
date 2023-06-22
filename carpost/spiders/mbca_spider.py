from carpost.filters import CarpostFilter
from carpost.items import CarpostItem
from urllib.parse import urlencode
from scrapy import Selector
from furl import furl
from pluck import pluck, ipluck
import argparse
import scrapy
import json
import logging
import math
import datetime



class MBCASpider(scrapy.Spider):
    name = 'MBCA'
    url = 'https://nafta-service.mbusa.com/api/inv/en_ca/used/vehicles/search?'
    detail_url = 'https://nafta-service.mbusa.com/api/inv/en_ca/used/vehicles/lookup/vin?vin='
    page_num = 0
    page_count = 100
    default_model = [
                    'C280W4','C300W4','C300W','C250W','C63','C350W','C400W4','C63P','C450W4','C350WE','C63WS','C43W4','C63W',
                    'E350W4','E63','E350W','E550W','E550W4','E350BTC','E250BTC4','E250BTC','E63P','E400W','E400W4','E63W4S','E250D','E43W4','E300W4','E300W','E300','E450W4','E53W4',
                    'B%20ED','B250E',
                    'A220W','A220W4','A35W4',
                    'GT63C4','GT63C4S','GT53C4',
                    'S500V4','S500V','S550V','S550V4','S63','S65V','S63V4','S600V','S550VE','S600X','S550X4','S450V','S560V','S650X','S560V4','S450V4','S560X4','S560VE',
                    'E350C','E550C','E350C4','E400C','E400C4','E53C4','E450C4','E450C',
                    'C350C','C350C4','C63C','C250C','C300C4','C63CS','C300C','C43C4',
                    'CLA250C','CLA250C4','CLA45','CLA45C4','CLA35C4','CL63','CLS63','CLS550C','CLS550C4','CLS63P','CLS400C','CLS400C4','CLS63C4S','CLS450C','CLS53C4','CLS450C4','CLK350C',
                    'GLC300C4','GLC63C4S','GLC63C4','GLC43C4','GLE450C4','GLE63C4S','GLE43C4','GLE53C4',
                    'S550C4','S63C4','S65C','S560C4',
                    'GTS','GT','GTR','GTC',
                    'SLSC','SLSGTC',
                    'CLK550A','CLK350A',
                    'E350A','E550A','E400A','E400A4','E450A','E53A4','E450A4',
                    'C300A','C300A4','C63AS','C43A4','C63A',
                    'S63A4','S65A','S550A','S560A',
                    'SLK350','SLK280','SLK300','SLK250','SLK55','SLC300R','SLC43R','SL550R','SL63','SL550','SL400','SL65','SL450R','SL63R',
                    'GTA','GTCA','GTRA',
                    'SLSR','SLSGTR',
                    'GLA45','GLA250W2','GLA250W4','GLA250W','GLA45W4','GLA35W4'
                    ]

    bodystyle = ['CPE','SUV','RDS','SDN','CAB']		

    def __init__(self, year=None, model=None, body=None, detail=None, *args, **kwargs):
        if year is not None:
            self.year = year
        else:
            self.year = datetime.datetime.now().year

        if body is not None:
            self.bodystyle = [body]
        else:
            self.bodystyle = self.bodystyle

        if model is not None:
            self.model = [model]
        else:
            self.model = self.default_model

        if detail is not None:
            self.detail = detail
        else:
            self.detail = None     

        super(MBCASpider, self).__init__(*args, **kwargs)

    def start_requests(self):
        if self.detail is not None:
            uri = furl(self.detail)
            vin = uri.path.segments[-1]
            yield scrapy.Request(url=self.detail_url+vin, callback=self.parse_item)
        mb_data = {
                # 只抓該年度
                'minYear':  self.year,
                'maxYear':  self.year,
                'model': ','.join(self.model),
                'bodystyle': ','.join(self.bodystyle),
                'start': self.page_num,
                'count': self.page_count,
                'resvOnly': 'false',
                'sortBy': 'distance',
                'zip': 'K1K 3B6',
                # 'lat': '45.4215296',
                # 'lng': '-75.69719309999999',
                'distance': 'ANY',
                'fuelType': 'G',
                'includeAllPreOwned': 'true',
                'invType':'all'
        }
    
        yield scrapy.Request(url=self.url+urlencode(mb_data), callback=self.parse_list)

    def parse_list(self, response):
        content = json.loads(response.text)
        paging = content.get('result').get('pagedVehicles').get('paging')
        total_count = paging.get('totalCount')
        url = response.request.url
        new_url = furl(url)
        num_start = 0
        if total_count < self.page_count:
            num_start = 1
        for num in range(num_start, total_count, self.page_count):
            new_url.args['start'] = num
            request_url = new_url.url
            
            yield scrapy.Request(url=request_url, callback=self.parse_vehicle)

    #車輛完整資料
    def parse_vehicle(self, response):
        res = json.loads(response.text)
        inventories = res.get('result').get('pagedVehicles').get('records')
        if len(inventories) > 0:
           for data in inventories:
                vin = data.get('vin')
                yield scrapy.Request(url=self.detail_url+vin, callback=self.parse_item)

    def parse_item(self, response):
        res = json.loads(response.text)
        vehicles = res.get('result').get('vehicle')
        if len(vehicles) > 0:
            vehicle_data = vehicles.get('usedVehicleAttributes')
            dealerCode = CarpostFilter.getDealerCode(vehicle_data.get('dealer').get('name'))
            dealerId = vehicle_data.get('dealer').get('id')
            title = CarpostFilter.getTitle(vehicle_data.get('descriptionLabel'), vehicle_data.get('certified'))
            content_url = 'https://www.mercedes-benz.ca/en/cpo/inventory/vehicle/'+str(dealerCode)+'/'+str(dealerId)+'/'+str(vehicles.get('classId'))+'/'+str(vehicles.get('bodystyleId'))+'/'+str(vehicles.get('modelId'))+'/'+str(vehicles.get('vin'))
            features = pluck(vehicle_data.get('optionList'), 'text')  #配備只有一區

            images = None
            if vehicle_data.get('images') is not None:
                images = vehicle_data.get('images')

            item = CarpostItem()
            item['data_from']       = 'MBCA'
            item['year']            = vehicles.get('year')
            item['vin']             = vehicles.get('vin')
            item['make']            = 'Mercedes-Benz'
            item['model']           = vehicles.get('modelId').replace(" ", "")
            item['trim']	        = ''     #補
            item['bodystyle']	    = vehicles.get('bodyStyleName')
            item['title']           = title
            
            item['price']           = vehicle_data.get('dsrp') * 0.82
            item['mileage']         = vehicle_data.get('mileage') * 0.62137   #統一轉回英哩
            item['location']        = vehicle_data.get('dealer').get('address')[0]['state']
            item['country']         = vehicle_data.get('dealer').get('address')[0]['country']
            
            item['highway_mpg']     = ''
            item['city_mpg']        = ''
            item['drivetrain']      = ''
            item['transmission']    = vehicle_data.get('driveTrain').get('text')
            
            item['dealer']          = vehicle_data.get('dealer').get('name')
            item['in_color']        = vehicles.get('upholstery').get('name')
            item['ex_color']        = vehicles.get('paint').get('name')
            
            item['url']             = content_url
            item['engine']          = ''

            item['feature']         = features
            item['images']          = images

            yield item