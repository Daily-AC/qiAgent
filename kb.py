# -*- coding:utf-8 -*-
import hashlib
import base64
import hmac
import time
from urllib.parse import urlencode
import json
import websocket
import _thread as thread
import ssl

class Document_Q_And_A:
    def __init__(self, APPId, APISecret, TimeStamp, OriginUrl):
        self.appId = APPId
        self.apiSecret = APISecret
        self.timeStamp = TimeStamp
        self.originUrl = OriginUrl

    def get_origin_signature(self):
        m2 = hashlib.md5()
        data = bytes(self.appId + self.timeStamp, encoding="utf-8")
        m2.update(data)
        checkSum = m2.hexdigest()
        return checkSum

    def get_signature(self):
        # 获取原始签名
        signature_origin = self.get_origin_signature()
        # 使用加密键加密文本
        signature = hmac.new(self.apiSecret.encode('utf-8'), signature_origin.encode('utf-8'),
                             digestmod=hashlib.sha1).digest()
        # base64密文编码
        signature = base64.b64encode(signature).decode(encoding='utf-8')
        return signature

    def get_header(self):
        signature = self.get_signature()
        header = {
            "Content-Type": "application/json",
            "appId": self.appId,
            "timestamp": self.timeStamp,
            "signature": signature
        }
        return header

    def get_url(self):
        signature = self.get_signature()
        return self.originUrl + "?" + f'appId={self.appId}&timestamp={self.timeStamp}&signature={signature}'

    def get_body(self, question):
        data = {
            "chatExtends": {
                "wikiPromptTpl": "请将以下内容作为已知信息：\n<wikicontent>\n请根据以上内容和以下用户给出的简历信息给出和给岗位初步匹配的20个序列号并组成列表，无需输出多余信息\n简历信息:<wikiquestion>\n回答:",
                "wikiFilterScore": 0.83,
                "temperature": 0.5
            },
            "fileIds": [
                "xxx"
            ],
            "messages": [
                {
                    "role": "user",
                    "content": question
                }
            ]
        }
        return data

class DocumentQAClient:
    def __init__(self, app_id, api_secret):
        self.APPId = app_id
        self.APISecret = api_secret
        self.OriginUrl = "wss://chatdoc.xfyun.cn/openapi/chat"
        self.answer_content = ""
        self.completed = False
        self.error_occurred = False

    def on_error(self, ws, error):
        print("### error:", error)
        self.error_occurred = True
        self.completed = True

    def on_close(self, ws, close_status_code, close_msg):
        # print("### closed ###")
        self.completed = True

    def on_open(self, ws):
        thread.start_new_thread(self.run, (ws,))

    def run(self, ws):
        data = json.dumps(ws.question)
        ws.send(data)

    def on_message(self, ws, message):
        data = json.loads(message)
        code = data['code']
        if code != 0:
            print(f'请求错误: {code}, {data}')
            self.error_occurred = True
            ws.close()
        else:
            content = data["content"]
            status = data["status"]
            self.answer_content += content
            if status == 2:
                ws.close()

    def get_jobs_info(self, question):
        """
        获取工作信息的接口
        :param question: 问题字符串
        :return: 答案字符串
        """
        curTime = str(int(time.time()))
        document_Q_And_A = Document_Q_And_A(self.APPId, self.APISecret, curTime, self.OriginUrl)
        
        wsUrl = document_Q_And_A.get_url()
        body = document_Q_And_A.get_body(question)
        
        # 重置状态
        self.answer_content = ""
        self.completed = False
        self.error_occurred = False
        
        # 禁用WebSocket库的跟踪功能
        websocket.enableTrace(False)
        ws = websocket.WebSocketApp(wsUrl, 
                                   on_message=self.on_message, 
                                   on_error=self.on_error, 
                                   on_close=self.on_close, 
                                   on_open=self.on_open)
        ws.question = body
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        
        # 等待请求完成
        while not self.completed:
            time.sleep(0.1)
            
        # if self.error_occurred:
        #     return "请求过程中出现错误，请检查网络连接或API配置"
        
        return self.answer_content

# 使用示例
if __name__ == '__main__':
    # 配置信息
    APPId = "xxx"
    APISecret = "xxx"
    
    # 创建客户端实例
    client = DocumentQAClient(APPId, APISecret)
    
    # 调用接口获取信息
    question = """
{
  "recommended_positions": ["C++开发工程师", "Python全栈开发", "AI应用开发工程师", "分布式系统工程师"],
  "technical_keywords": ["C++17/20", "Python", "PyTorch", "分布式系统", "LLM", "Qt", "Boost.Asio"],
  "experience_level": "初级",
  "industry_focus": ["人工智能", "即时通讯", "智能家居", "互联网"],
  "location_preferences": ["长沙", "杭州", "深圳"],
  "education_requirements": "本科",
  "skill_matches": {
    "programming_languages": ["C++", "Python"],
    "frameworks_tools": ["Qt", "PyTorch", "FastAPI", "Redis", "MySQL"],
    "specializations": ["高并发系统", "AI集成", "语音识别", "分布式架构"]
  },
  "priority_filters": {
    "must_have": ["C++或Python开发经验", "本科在读或学历"],
    "nice_to_have": ["AI项目经验", "分布式系统经验", "获奖经历"]
  }
}
"""
    answer = client.get_jobs_info(question)
    print("问题:", question)
    print("答案:", answer)
