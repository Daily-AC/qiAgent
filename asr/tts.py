# 从aip模块中导入AipSpeech类，这是百度提供的一个用于语音处理的类。  
from aip import AipSpeech
from asr.process_text import merge_md_paragraphs
from asr.playsnd import playsnd
from playsound import playsound
from pydub import AudioSegment
import os

# 下面的三行代码定义了连接到百度AIP服务所需的三个关键参数：APP_ID、API_KEY和SECRET_KEY。  
# 这些参数是用于身份验证的，确保只有授权的用户才能访问服务。  
APP_ID='Your APP ID'  
API_KEY='Your API Key'  
SECRET_KEY='Your Secret Key'  
# 发音人选择, 基础音库：0为度小美，1为度小宇，3为度逍遥，4为度丫丫，
# 精品音库：5为度小娇，103为度米朵，106为度博文，110为度小童，111为度小萌，默认为度小美 
PER = 5118
# 语速，取值0-15，默认为5中语速
SPD = 6.5
# 音调，取值0-15，默认为5中语调
PIT = 5
# 音量，取值0-9，默认为5中音量
VOL = 5
# 下载的文件格式, 3：mp3(default) 4： pcm-16k 5： pcm-8k 6. wav
AUE = 3
# 使用上面定义的三个参数来初始化AipSpeech类的一个实例，命名为client。  
# 这个实例将用于后续与百度AIP服务的交互。  
client=AipSpeech(APP_ID, API_KEY, SECRET_KEY)  

# 定义合成后的语音文件将要保存的路径和文件名。  
def getifp(i):
    return f"asr/Temp/temp{i}.mp3"

def merge_mp3_binary(input_files, output_file):
    with open(output_file, "wb") as outfile:
        for file in input_files:
            with open(file, "rb") as infile:
                outfile.write(infile.read())

def merge(mp3_files, output_file):
    # 初始化合并后的音频对象
    combined = AudioSegment.empty()

    for file in mp3_files:
        audio = AudioSegment.from_mp3(file)
        combined += audio  # 拼接音频

    # 导出合并后的文件
    combined.export(output_file, format="mp3")
    print(f"合并完成！输出文件: {output_file}")


def t2s(Text):
    if not Text or Text == -1:
        return None
    Text = merge_md_paragraphs(Text)
    print(Text)
    # 调用client的synthesis方法来进行语音合成。参数包括要合成的文本、语言类型（这里是中文'zh'）、语音的音量（这里是5）等。 
    # 方法的返回值将是一个二进制数据（如果合成成功）或一个字典（如果发生错误）。  
    texts = split_string(Text)
    cnt = 0
    # 打印分割后的字符串
    for i, text in enumerate(texts):
        cnt = cnt + 1
        result=client.synthesis(text, 'zh', 1, {'vol': VOL, 'spd': SPD, 'pit': PIT, 'per': PER, 'aue': AUE})  
        
        # 打印出合成操作的结果，这可能是二进制数据或一个错误字典。  
        # print(result)  
        
        # 下面的代码块检查返回的结果是否是一个字典。如果是字典，那么很可能是一个错误信息。  
        # 如果不是字典，那么结果应该是包含合成语音的二进制数据。  
        if not isinstance(result, dict):  
            # 如果结果不是字典（即没有错误），则打开指定的文件路径，并将合成的语音数据写入文件。  
            # 'wb'模式表示以二进制写模式打开文件。  
            with open(getifp(i),'wb') as f:  
                f.write(result)  # 将语音数据写入文件。  
        else:  
            # 如果结果是字典，那么打印“错误”，表示语音合成过程中可能出现了问题。  
            print("错误")

    # merge_mp3_binary([getifp(i) for i in range(cnt)], "./Temp/temp.mp3")

    for i in range(cnt):
        try:
            playsnd(getifp(i))
        except Exception as e:
            print(f"error:{e}")
    
    for i in range(cnt):
        os.remove(getifp(i))
    
    # playsnd("./Temp/temp.mp3")
    # os.remove("./Temp/temp.mp3")

def split_string(input_string, chunk_size=200):
    return [input_string[i:i+chunk_size] for i in range(0, len(input_string), chunk_size)]

str = \
"""
宝宝肚肚打雷啦
"""

if __name__ == "__main__":
    t2s(str)
