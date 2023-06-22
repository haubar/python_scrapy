# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

from scrapy.exceptions import DropItem
import pymysql
import logging

class FilterPipeline:
    def process_item(self, item, spider):
        if spider.name == 'BMWUSASpider':
            item['data_from'] = 'BMWUSA' 
            pass

        elif spider.name == 'MBUSASpider':
            item['data_from'] = 'MBUSA' 
            pass

        elif spider.name == 'MBCASpider':
            item['data_from'] = 'MBCA' 
            pass

        elif spider.name == 'CARSSpider':
            item['data_from'] = 'CARS' 
            pass

        elif spider.name == 'AUTOTRADERSpider':
            item['data_from'] = 'AUTOTRADER' 
            pass

        elif spider.name == 'AUTOTRADERCASpider':
            item['data_from'] = 'AUTOTRADERCA' 
            pass
        else:
            pass
        
        return item



class DeleteNullPipeline:
    def process_item(self, item, spider):
        if item['images'] is None:
            raise DropItem(f'[{item["images"]}] 沒有圖片')
        if item['feature'] is None:
            raise DropItem(f'[{item["feature"]}] 沒有配備')
        if item['year'] is None:
            raise DropItem(f'[{item["year"]}] 沒有年份')
        if item['vin'] is None:
            raise DropItem(f'[{item["vin"]}] 沒有vin code')
        if item['title'] is None:
            raise DropItem(f'[{item["title"]}] 沒有車輛說明')
        if item['url'] is None:
            raise DropItem(f'[{item["url"]}] 沒有對應網址')
        if item['price'] is None:
            raise DropItem(f'[{item["price"]}] 沒有價錢')
        if item['mileage'] is None:
            raise DropItem(f'[{item["mileage"]}] 沒有哩程')
        if item['engine'] is None:
            raise DropItem(f'[{item["engine"]}] 沒有engine')
        if item['model'] is None:
            raise DropItem(f'[{item["model"]}] 沒有車型model')
        if item['make'] is None:
            raise DropItem(f'[{item["make"]}] 沒有廠牌make')
        if item['dealer'] is None:
            raise DropItem(f'[{item["dealer"]}] 沒有dealer')
        return item


# 存入mysql
class MySqlPipeline(object):

    def open_spider(self, spider):
        db = spider.settings.get('MYSQL_DB_NAME')
        host = spider.settings.get('MYSQL_DB_HOST')
        port = spider.settings.get('MYSQL_PORT')
        user = spider.settings.get('MYSQL_USER')
        password = spider.settings.get('MYSQL_PASSWORD')
        
        # Database Connecting
        self.connection = pymysql.connect(
            host = host,
            user = user,
            password= password,
            db = db,
            cursorclass= pymysql.cursors.DictCursor
        )
        print('Connect to db ::', host, db)
    def close_spider(self, spider):
        print('close  db ::', host, db)
        self.connection.close()
    def process_item(self, item, spider):
        # print("------------最終資料---------------------")
        # print(item)
        # print("------------最終資料---------------------")
        self.insert_to_mysql(item)
        return item
    def insert_to_mysql(self, item):
        values = (
                pymysql.escape_string(str(item['data_from'])),
                pymysql.escape_string(str(item['year'])),
                pymysql.escape_string(str(item['vin'])),
                pymysql.escape_string(str(item['make'])),
                pymysql.escape_string(str(item['model'])),
                pymysql.escape_string(str(item['trim'])),
                pymysql.escape_string(str(item['bodystyle'])),
                pymysql.escape_string(str(item['title'])),
                pymysql.escape_string(str(item['price'])),
                pymysql.escape_string(str(item['mileage'])),
                pymysql.escape_string(str(item['location'])),
                pymysql.escape_string(str(item['highway_mpg'])),
                pymysql.escape_string(str(item['city_mpg'])),
                pymysql.escape_string(str(item['drivetrain'])),
                pymysql.escape_string(str(item['transmission'])),
                pymysql.escape_string(str(item['dealer'])),
                pymysql.escape_string(str(item['in_color'])),
                pymysql.escape_string(str(item['ex_color'])),
                pymysql.escape_string(str(item['url'])), 
                pymysql.escape_string(str(item['engine'])),
                pymysql.escape_string(str(item['feature'])),
                pymysql.escape_string(str(item['images']))
        )
        with self.connection.cursor() as cursor:
            sql = "INSERT INTO cars (`data_from`, `year`, `vin`, `make`, `model`, `trim`, `bodystyle`, `title`, `price`, `mileage`, `location`, `highway_mpg`, `city_mpg`, `drivetrain`, `transmission`, `dealer`, `in_color`, `ex_color`, `url`, `engine`, `feature`, `images`) VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')"
            cursor.execute(sql % values)
            self.connection.commit()
            print("insert to db")