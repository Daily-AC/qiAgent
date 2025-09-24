from qibot import create_qiBot_from_config
from asr.stt import s2t
from asr.tts import t2s

async def main():
    agent = create_qiBot_from_config(type="interviewBot")
    job_info = \
    """
    {
        "title": "C\\C++\\JAVA\\python\\ （全国多城市可安排）",
        "salary": "15-25K·14薪",
        "position": "杭州",
        "experience": "经验不限",
        "degree": "本科",
        "tags": "Golang,Java,C++,C,Python",
        "describe": "岗位职责:1. 负责华为终端有限公司的软件开发与维护工作2. 参与系统设计，确保代码质量和系统稳定性3. 与团队合作，完成项目需求分析及模块划分任职要求：1. 精通CC++、JAVA、Python等编程语言2. 具备良好的逻辑思维能力和问题解决能力3. 能够适应全国多城市的工作安排，具有较强的沟通协调能力",
        "company_name": "华为终端有限公司",
        "scale": "10000人以上",
        "industry": "互联网"
    }
    """

    interview_info = \
    """
    {
        "difficulty": "中等",
        "round": "技术面"
    }
    """

    all_info = "面试的岗位信息：\n" + job_info + "\n面试信息：\n" + interview_info

    messages = [
        {
            "role": "system",
            "content": agent.system_prompt
        },
    ]

    await agent.startMCP("./mcp_server/mcp_server.py")  # 启动MCP服务器

    res = ""
    # async for chunk in agent.process_query_stream(all_info, messages, True):
    #     if chunk.strip() == "":
    #         continue
    #     # t2s(chunk)
    #     # print(chunk, end='', flush=True)
    #     res += chunk
    res = await agent.process_query(all_info, messages)
    t2s(res)
    print("\n")
    messages.append({"role": "assistant", "content": res})

    try:
        while True:
            res = ""
            user_input = s2t()  # 语音转文本
            if user_input is None:
                continue
            if "结束" in user_input:
                break
            messages.append({"role": "user", "content": user_input})
            # async for chunk in agent.process_query_stream(messages, True):
            #     # t2s(chunk)
            #     # print(chunk, end='', flush=True)
            #     res += chunk
            res = await agent.process_query(user_input, messages)
            t2s(res)
            print("\n")
            messages.append({"role": "assistant", "content": res})
    except KeyboardInterrupt:
        print("对话结束。")
    finally:
        await agent.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())