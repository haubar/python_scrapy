import datetime
import re
import requests
import json
import logging
class CarpostFilter():
        


#-------------------------- mbusa  -------------------------------#		

    # 取得dealer code
    def getDealerCode(data):
        dealerCode = data.replace(' ','-').replace(',','').replace('.','')
        return dealerCode

    # 產生真實瀏覽頁連結
    def getDetailUrl():
        params_query = ''
        url = 'https://www.mbusa.com/en/cpo/inventory/vehicle/'+params_query
        pass
    
    def getAllFeature():
        pass


    def getTitle(label, cpo):

        title = label
        if cpo:
            title = 'Certified' + ' ' + title
        return title

    def getEnge(value):
        for data in value:
            if 'Engine' in data:
                return data

    def getCyl(value):
        for data in value:
            if 'Inline-' in data:
                return data            

#-------------------------- bmwusa  -------------------------------#			

    # 取得資料內指定key的集合
    def getVins(lists ,key):
        data = []
        for item in lists:
            data.append(item.get(key))
        return list(data)
    
    # 取得token
    def getBMWUSAtoken():
        url = 'https://inventoryservices.bmwdealerprograms.com/token'
        data = {'grant_type':'password','username':'BMWInventory@criticalmass.com','password':'1nv3nt0ry!2020'}
        response = requests.post(url = url, data = data)
        content = json.loads(response.text)
        token = content['access_token']
        return token


    # 產生目前年份的範圍陣列
    @staticmethod
    def getSearchYear():
        now = datetime.datetime.now()
        min =  now.year - 4
        max =  now.year + 1
        return list(range(min, max))


    def getModel(name, description):
        return name if name is not None else description


    def getEngineDES(displacement, description):
        return displacement if displacement !='0.0' else description

# ------------------------------ CARS ----------------------------------#
    def getEngine(description):
        return description.split()[0] if description else ''


# ------------------------------ common ----------------------------------#
    def checkType(value):
        if value is None:
            value = ''
        return value



    def formatEngine(value):
        data = re.findall("\d+\.\d+", value)
        return data[0] if len(data) > 0 else ''

    def formatCyl(value):
        data = re.findall("Inline-\d+", value)
        return data[0].replace('Inline-','') if len(data) > 0 else ''

    def formatMile(value):
        return int(value.replace(',','').replace('miles','').strip())

    def formatKm(value):
        data = int(value.replace(',','').replace('km','').strip())
        return data
    
    # 轉換 L/100km
    def formatLKM(value):
        data = float(re.findall("\d+\.\d+", value))
        return data[0] if len(data) > 0 else ''

    #mpg 轉換
    def formatMpg(value):
        return int((3.7854/((float(value)*1.61)/100)))
        