# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class CarpostItem(scrapy.Item):
  
	#資料來源(cars.com、bmwusa、mbusa)
	data_from = scrapy.Field()
	#車子年份
	year = scrapy.Field()
	#車子vin
	vin = scrapy.Field()
	#廠牌
	make = scrapy.Field()
	#車型
	model = scrapy.Field()
	#trim - 備用
	trim = scrapy.Field()
	#body - 備用
	bodystyle = scrapy.Field()   
	#用來顯示的車子標題
	title = scrapy.Field()
	#當地價格
	price = scrapy.Field()
	#車子里程
	mileage = scrapy.Field()
	#車子所在地（各區縮寫）
	location = scrapy.Field()
	#車子所在國（各國縮寫）	
	country = scrapy.Field()	
	#高速公路油耗（不影響車價，可能空值）
	highway_mpg = scrapy.Field()
	#市區油耗（不影響車價，可能空值）
	city_mpg = scrapy.Field()
	#動力（不影響車價，可能空值）
	drivetrain = scrapy.Field()
	#傳動（不影響車價，可能空值）
	transmission = scrapy.Field()
	#氣缸數（不影響車價，可能空值）
	cylinders = scrapy.Field()
	#車商
	dealer = scrapy.Field()
	#內裝顏色
	in_color = scrapy.Field()
	#外裝顏色
	ex_color = scrapy.Field()
	#車子內頁網址
	url = scrapy.Field()
	#引擎大小
	engine = scrapy.Field()
	#車子配備（可能空值，空值要踢除）
	feature = scrapy.Field()
	#車子圖片（可能空值，空值要踢除）
	images = scrapy.Field()
	pass