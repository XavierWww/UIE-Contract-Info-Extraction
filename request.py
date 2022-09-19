# -*- coding: utf-8 -*-

'''
@Author: Xavier WU
@Date: 2022-07-19
@LastEditTime: 2022-08-30
@Description: This file is contract info extraction client. 
@All Right Reserve
'''

import requests
import json

url = 'http://192.168.50.121:8282/contract_info_extraction'     # 服务地址（ocr后的结果）
url = "http://192.168.50.121:8282/contract_info_extraction_pdf" # 服务地址（pdf合同）

input_data = [
        '''
        合同编号：FXTZ/XY2020XXXX
        ''',
        '''
        深圳大学附属教育集团外国语小学食材配送服务合同
        甲方： 深圳大学附属教育集团外国语小学
        乙方： 深圳市仲康时代餐饮有限公司
        根据深圳市政府采购中心 0832-SFCX21FSC164 号招标项目的投标结果，由深
        圳市仲康时代餐饮有限公司为中标方。按照《中华人民共和国民法典》和《深圳经
        济特区政府采购条例》，经深圳大学附属教育集团外国语小学（以下简称甲方）和
        ''',
        '''
        深圳市仲康时代餐饮有限公司（以下简称乙方）协商，就甲方委托乙方承担 深圳
        大学附属教育集团外国语小学食材配送服务项目，达成以下合同条款：
        第一条 项目概况
        ''',
        '''
        项目名称：深圳大学附属教育集团外国语小学食材配送服务项目
        项目内容： 深圳大学附属教育集团外国语小学食堂主食、副食配送服务
        服务时间：2021 年 8 月 17 日-2022 年 8 月 16 日，本项目为长期服务类项目，
        第一年为本次招标的中标服务期限，采购人可根据项目需求和中标供应商的履约情
        况确定合同期限是否延长，但最长不超过三年。
        ''',
        '''
        合同价款：合同总价为 450000*0.97=436500 元，含一切税费。本合同总价包
        括乙方为实施本项目所需的服务和技术费用等，为固定不变价格，且不随通货膨胀
        的影响而波动。合同总价包括乙方履行本合同义务所发生的一切税费、费用和支出。
        如发生本合同规定的不可抗力，合同总价可经双方友好协商予以调整。'''
]

input_data = './data/杭州日晟-原始稿-杨晓青.pdf'

resp = requests.request("POST", url, data=json.dumps(input_data)) 
print(json.dumps(resp.json(), ensure_ascii=False, indent=4))