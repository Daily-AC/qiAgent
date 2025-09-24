from pdfprocessor import PDFProcessor
from qibot import create_qiBot_from_config, qiBot
import logging
import os
import time

mcp_server_path = "./mcp_server/mcp_server.py" # 请替换为你的mcp_server.py路径

async def main(pdf_path):
    # # 1.提取pdf简历信息
    # print("⌛️开始提取简历信息...")
    # pdf_processor = PDFProcessor()
    # pdf_content = pdf_processor.extract_text_from_pdf(pdf_path)
    # print("✅提取简历信息成功！")

    # # 2.获取json化的简历信息
    # print("⌛️开始获取json化简历信息...")
    # resumeBot = create_qiBot_from_config(type="resumeBot")
    # resume_json = await resumeBot.process_query(pdf_content)
    # await resumeBot.close()
    # print("✅获取json化简历信息成功！")

    # # 将json化简历信息保存到本地，方便调试
    # with open("./output/resume.json", "w", encoding="utf-8") as f:
    #     f.write(resume_json)
    #     print("👌保存json化简历信息到./output/resume.json")

    # # 3.根据简历信息匹配最佳岗位
    # print("⌛️开始匹配最佳岗位...")
    # matchingBot = create_qiBot_from_config(type="matchingBot")
    # await matchingBot.startMCP(mcp_server_path)
    # result = await matchingBot.process_query(query=resume_json)
    # await matchingBot.close()
    # print("✅匹配最佳岗位成功！")

    # # 将匹配结果保存到本地，方便调试
    # with open("./output/result.md", "w", encoding="utf-8") as f:
    #     f.write(result)
    #     print("👌保存匹配结果到./output/result.md")

    # 4.将md结果转化为pdf
    print("⌛️开始将结果转化为pdf...")
    pdf_processor = PDFProcessor()
    pdf_processor.md_to_pdf("./output/result.md", "./output/result.pdf")
    print("✅pdf结果生成成功！请查看./output/result.pdf")
    
    return "✅pdf结果生成成功！请查看./output/result.pdf"

if __name__ == "__main__":
    pdf_path = "./resume/resume.pdf" # 请替换为你的pdf简历路径
    import asyncio
    asyncio.run(main(pdf_path))