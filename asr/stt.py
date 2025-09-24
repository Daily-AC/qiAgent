import speech_recognition as sr

def recognize_speech_from_mic(recognizer, microphone):
    """转录来自麦克风的语音"""

    if not isinstance(recognizer, sr.Recognizer):
        raise TypeError("`recognizer` 必须是 `Recognizer` 实例")

    if not isinstance(microphone, sr.Microphone):
        raise TypeError("`microphone` 必须是 `Microphone` 实例")

    # 用adjust_for_ambient_noise 来消除环境噪音，read_timeout 秒内未检测到任何语音时，停止录音。
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source) # only do this once!
        #recognizer.energy_threshold = 4000  # 或者手动调整能量阈值
        recognizer.dynamic_energy_threshold = True  # 动态调整能量阈值以适应变化的环境噪音
        recognizer.dynamic_energy_adjustment_damping = 0.15 # 动态能量调整的阻尼因子，降低调整速度，避免过度调整
        recognizer.dynamic_energy_ratio = 1.5 #  信噪比

        print("请开始说话...")
        audio = recognizer.listen(source, phrase_time_limit=60) #调整录音时间10秒


    # 设置响应消息
    response = {
        "success": True,
        "error": None,
        "transcription": None
    }

    # 尝试识别语音，超时或网络等情况会报错
    try:
        response["transcription"] = recognizer.recognize_google(audio, language="zh-CN") # 根据需要修改语言

    except sr.RequestError:
        # API was unreachable or unresponsive
        response["success"] = False
        response["error"] = "API 不可达或无响应"
    except sr.UnknownValueError:
        # speech was unintelligible
        response["error"] = "无法识别语音"
    except Exception as e:  #处理其它异常情况
         response["success"] = False
         response["error"] = f"发生其他错误：{e}"



    return response


def s2t():
    # 创建识别器和麦克风实例
    recognizer = sr.Recognizer()
    microphone = sr.Microphone() # 可以通过sr.Microphone.list_microphone_names()来获取麦克风设备名

    #调用录音
    response = recognize_speech_from_mic(recognizer, microphone)
    if not response["success"]:
        print(f"发生错误: {response['error']}")
        return None

    # show the user what the transcribes
    print("你说： {}".format(response["transcription"]))
    return response["transcription"]

if __name__ == "__main__":
    # 创建识别器和麦克风实例
    recognizer = sr.Recognizer()
    microphone = sr.Microphone() # 可以通过sr.Microphone.list_microphone_names()来获取麦克风设备名

    while True: #一直转录，直到手动停止
        #调用录音
        response = recognize_speech_from_mic(recognizer, microphone)
        if not response["success"]:
            print(f"发生错误: {response['error']}")
            continue

        # show the user what the transcribes
        print("你说： {}".format(response["transcription"]))
        if(response["transcription"]=="停止"):
            break # 说“停止”时，停止循环

