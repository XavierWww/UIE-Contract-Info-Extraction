'''
@Author: Xavier WU
@Date: 2022-07-19
@LastEditTime: 2022-08-31
@Description: This file is contract info extraction server. 
@All Right Reserve
'''

import sanic.response
from collections import OrderedDict
from collections import defaultdict
import json
from sanic import Sanic
from paddlenlp import Taskflow
import re
from datetime import datetime
from ordered_set import OrderedSet
import pdfplumber

class TaskExtractionService:
    
    def __init__(self, name, host, port):
        
        self.host = host
        self.port = port
        self.app = Sanic(name)
        self.app_add_routes()
        self.response = None

        '''
        {
            "parties":[],         # 签约双方/多方主体名称
            "start_date":"",      # 合同开始时间，返回时统一格式为 yyyy-MM-DD; 如：2021年3月20日
            "end_date":"",        # 合同结束时间，返回时统一格式为 yyyy-MM-DD; 如：2021年3月20日
            "contract_number":"", # 合同编号
            "status":""           # 合同状态
        }
        ''' 
        
        self.label = ["合同编号", "开始时间", "结束时间", "签约双方", "合同状态"]
        self.schema = ['开始时间', '结束时间', '合同编号', '组织']
        self.acc = 0.01
        self.threshold = 0.01

        self.ie = Taskflow('information_extraction', schema=self.schema, position_prob=self.acc, device_id=1, task_path='./checkpoint/model_best2')
        self.app.run(host=self.host, port=self.port)

    def app_add_routes(self):
        
        self.app.add_route(self.info_extraction, "/contract_info_extraction", methods=["POST"])
        self.app.add_route(self.info_extraction_pdf, "/contract_info_extraction_pdf", methods=["POST"])

    
    def get_pdf_info_extraction_result(self, pdf_path):
        
        raw_text = self.get_raw_texts(pdf_path)
        return raw_text
        
    def info_extraction_pdf(self, request):
        
        init_vocab = '[\\[\\]{《》}【】]'
        text_path = request.body.decode('utf-8')
        file_path = json.loads(text_path)
        raw_text = self.get_pdf_info_extraction_result(pdf_path=file_path)
        
        party_outputs = self.party_process(raw_text)
        number_outputs, number_outputs2 = self.number_process(raw_text)
        raw_text = [re.sub(init_vocab, " ", t) for t in raw_text]  
        
        uie_outputs = self.ie(raw_text)         # 抽取
        new_outputs = self.process(uie_outputs) # 后处理
        extraction = self.transfer(new_outputs) # 转换成字典
        results = self.merge(extraction, party_outputs, number_outputs, number_outputs2)    # 合并
        return sanic.response.json(results, ensure_ascii=False)
                
    def info_extraction(self, request):

        init_vocab = '[\\[\\]{《》}【】]'
        raw_text = request.body.decode('utf-8')
        raw_text = json.loads(raw_text)
        
        party_outputs = self.party_process(raw_text)
        number_outputs, number_outputs2 = self.number_process(raw_text)  
        raw_text = [re.sub(init_vocab, " ", t) for t in raw_text]
        
        uie_outputs = self.ie(raw_text)         # 抽取
        new_outputs = self.process(uie_outputs) # 后处理
        extraction = self.transfer(new_outputs) # 转换成字典
        results = self.merge(extraction, party_outputs, number_outputs, number_outputs2)    # 合并
        return sanic.response.json(results, ensure_ascii=False)
                                           
    '''
        将结果进行合并
    '''
    def merge(self, new_list, party_set, number_list, number_list2): # label = ["合同编号", "开始时间", "结束时间", "签约双方", "合同状态"]
        
        # 将相同类别的实体进行去重合并
        setdic = defaultdict(set)
        orgs = []
        for dic in new_list:
            for s in self.schema:
                if dic[s] != " ":  
                    if s != '组织':
                        setdic[s].add(dic[s])
                    else:
                        orgs.append(dic[s])
        setdic['组织'] = OrderedSet(orgs)
    
        # 构造新的返回结果
        ord_dic = OrderedDict()
        for s in self.label:
            
            if s == '合同编号': # 若无编号赋空值
                
                if number_list and setdic.get(s):
                    
                    temp_no = setdic[s].pop()
                    
                    if temp_no in number_list[0]: ord_dic[s] = number_list[0]
                    
                    else: ord_dic[s] = temp_no
                
                elif number_list2 and setdic.get(s):
                    
                    temp_no = setdic[s].pop()
                    
                    if temp_no in number_list2[0]: ord_dic[s] = number_list2[0]
                    
                    else: ord_dic[s] = temp_no
                    
                elif not number_list and not number_list2 and setdic.get(s):
                    
                    ord_dic[s] = setdic[s].pop()
                
                elif not setdic.get(s):
                    
                    if number_list: ord_dic[s] = number_list[0]
                    
                    elif number_list2: ord_dic[s] = number_list2[0]
                
                else:
                    ord_dic[s] = ""
  
            elif s == '开始时间':
                
                if setdic.get(s):
                    
                    s_time = []
                    for i in setdic[s]:
                        try:
                            s_time.append(datetime.strptime(i, "%Y-%m-%d"))
                        except:
                            try:
                                s_time.append(datetime.strptime(i, "%Y-%m"))
                            except:
                                s_time.append(datetime.strptime(i, "%Y"))
                    try:
                        ord_dic[s] = min(s_time).strftime("%Y-%m-%d") # 取最远的时间点
                    except:
                        try:
                            ord_dic[s] = min(s_time).strftime("%Y-%m") # 取最远的时间点
                        except:
                            ord_dic[s] = min(s_time).strftime("%Y") # 取最远的时间点
                        
                else:
                    ord_dic[s] = ""
                
            elif s == '结束时间':

                if setdic.get(s):
                    
                    e_time = []
                    for i in setdic[s]:
                        try:
                            e_time.append(datetime.strptime(i, "%Y-%m-%d"))
                        except:
                            try:
                                e_time.append(datetime.strptime(i, "%Y-%m"))
                            except:
                                e_time.append(datetime.strptime(i, "%Y"))
            
                    try:
                        ord_dic[s] = max(e_time).strftime("%Y-%m-%d") # 取最近的时间点
                    except:
                        try:
                            ord_dic[s] = max(e_time).strftime("%Y-%m") # 取最近的时间点
                        except:
                            ord_dic[s] = max(e_time).strftime("%Y")
                        
                else:
                    ord_dic[s] = ""

            elif s == '签约双方':
                
                ord_dic[s] = []
                if party_set:
                    temp = party_set & setdic['组织'] 
                else:
                    temp = setdic['组织']
                ord_dic[s] = list(temp)[:2] # 当前返回两个
                
            elif s == '合同状态':

                if setdic.get('结束时间'):
                      
                    time = []
                    # 合并时间信息
                    if setdic.get('开始时间'):
                        time = list(setdic['开始时间'] | setdic['结束时间'])
                    else:
                        time = list(setdic['结束时间'])
                    
                    # 转换时间类型取出最近时间点
                    date_time = []
                    for t in time:
                        try:
                            date_time.append(datetime.strptime(t, "%Y-%m-%d"))
                        except:
                            try:
                                date_time.append(datetime.strptime(t, "%Y-%m"))
                            except:
                                date_time.append(datetime.strptime(t, "%Y"))
                            
                    prev = max(date_time)
                    
                    # 计算与当前时间
                    cur = datetime.now()
                    
                    if cur.year - prev.year < 0:
                        ord_dic[s] = "履约结束"
                    elif cur.year - prev.year == 0:
                        if cur.month - prev.month < 0:
                            ord_dic[s] = "履约结束"
                        elif cur.month - prev.month == 0:
                            if cur.day - prev.day < 0:
                                ord_dic[s] = "履约结束"
                            else:
                                ord_dic[s] = "履约中"
                        else:
                            ord_dic[s] = "履约中"
                    else:
                        ord_dic[s] = "履约中"
                          
                else: # 若无结束时间则无法判断履约状态
                    ord_dic[s] = ""
        
        return ord_dic
                
    '''
        按Task进行Json数据工程化
    '''
    def transfer(self, new_list): # 默认每个片段抽取出的每个实体类别个数为1（输入片段不需要太长）
        
        results = []
        for i in new_list:

            dic = OrderedDict()
            for s in self.schema:
                
                if (s == '开始时间' or s == '结束时间') and i[s][0]['text'] != ' ':
                    dic[s] = self.time_transfer(i[s][0]['text'])
                else:
                    dic[s] = i[s][0]['text'] # 若某些实体类别的个数超过1怎么办？
                
            results.append(dic)
        return results

    '''
        时间处理
    '''
    def time_process(self, text):

        def format1(text):
            
            try:
                datetime.strptime(text, "%Y年%m月%d日")
                return False
            except:
                try:
                    datetime.strptime(text, "%Y年%m月")
                    return False
                except:
                    try:
                        datetime.strptime(text, "%Y年")
                        return False
                    except:
                        return True

        def format2(text):
            
            try:
                datetime.strptime(text, "%Y-%m-%d")
                return False
            except:
                try:
                    datetime.strptime(text, "%Y-%m")
                    return False
                except:
                    try:
                        datetime.strptime(text, "%Y")
                        return False
                    except:
                        return True
        
        def format3(text):
            
            try:
                datetime.strptime(text, "%Y/%m/%d")
                return False
            except:
                try:
                    datetime.strptime(text, "%Y/%m")
                    return False
                except:
                    try:
                        datetime.strptime(text, "%Y")
                        return False
                    except:
                        return True
        
        def format4(text):
            
            try:
                datetime.strptime(text, "%Y.%m.%d")
                return False
            except:
                try:
                    datetime.strptime(text, "%Y.%m")
                    return False
                except:
                    try:
                        datetime.strptime(text, "%Y")
                        return False
                    except:
                        return True
        
        return format1(text) and format2(text) and format3(text) and format4(text)

    '''
        将所有时间格式转换成 2022-07-08 格式
    '''
    def time_transfer(self, text):

        if '-' not in text:
            if '/' in text:
                text = text.replace('/', '-')
            elif '.' in text:    
                text = text.replace('.', '-')
            else:
                text = re.sub(r'[年月]', '-', text).replace('日', "")
                
        if text[-1] == '-':
            text = text[:len(text)-1]
            
        return text
        
    '''
        编号处理
    '''
    def number_process(self, text):
        
        numbers = []
        for s in text:
   
            temp = re.findall(r'编\s*号：\s*[A-Za-z0-9/-]+', s)
            
            for t in temp:
                numbers.append(t.split('：')[1].strip().replace(" ", "").replace("\n", ""))
                
        numbers2 = []
        for s in text:
   
            temp = re.findall(r'编\s*号:\s*[A-Za-z0-9/-]+', s)
            
            for t in temp:
                numbers2.append(t.split(':')[1].strip().replace(" ", "").replace("\n", ""))
        
        return numbers, numbers2

    '''
        双方处理
    '''
    def party_process(self, text):
        
        party = []
        for s in text:
            temp = re.findall(r'方（[\u4e00-\u9fa5]+）：\s*[\u4e00-\u9fa5（）]+|方：\s*[\u4e00-\u9fa5（）]+', s)
            for t in temp:
                party.append(t.split('：')[1].strip().replace(" ", "").replace("\n", ""))
        
        return OrderedSet(party)
    
    '''
        状态处理
    '''
    def status_process(self, text):
        
        pass
    
    '''
        对抽取结果进行后处理
    '''
    def process(self, uie_list):
        
        init_vocab = '[@!"#$%^&*()\+_~\\[\\];:?“”‘’。！,、·《》？【】__{|}<=>]'            
        new_list = []
        
        # 对每一条抽取结果里每个实体类别的抽取信息进行处理
        for dic in uie_list:
            
            new_dic = OrderedDict()
            for s in self.schema:
                
                if dic.get(s):
                    temp = []
                    for i in dic[s]:
                        
                        i['text'] = re.sub(init_vocab, "", i['text'].strip().replace(" ", "").replace("\n", ""))  # 抽取结果正则化去除特殊字符
                                                    
                        if (s == '开始时间' or s == '结束时间') and self.time_process(i['text']):
                            i['text'] = " "
                     
                        if s == '组织':
                            
                            if i.get('probability') and i['probability'] > 0.9:
                                temp.append(i)
                        
                        else:
                            if i.get('probability') and i['probability'] > self.threshold:  # 筛选掉低置信度结果
                                temp.append(i)
                         
                    if temp:    
                        new_dic[s] = temp
                    else: # 处理后若无抽取结果赋空值
                        new_dic[s] = [{'text': " "}]
                
                else: # 无抽取结果赋空值
                    new_dic[s] = [{'text': " "}]
                         
            new_list.append(new_dic)  
                
        return new_list

    '''
        解析PDF合同
    '''
    def get_raw_texts(self, pdf_path):
        texts = []
        with pdfplumber.open(pdf_path) as pdf:
            pages = pdf.pages
            for page in pages:
                s = page.extract_text()
                texts.extend(s.strip().split("。"))
                                    
        texts = [s for s in texts if len(s.strip())>0]
        return texts     
          
if __name__ == '__main__':
    host = '0.0.0.0' # 192.168.50.121 0.0.0.0
    port = 8080 # 8282 8080
    Service1 = TaskExtractionService('service', host, port)  # build service
     