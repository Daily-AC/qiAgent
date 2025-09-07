from qiagent.pdfprocessor import PDFProcessor
from qiagent.qibot import create_qiBot_from_config, qiBot
import logging
import os
import time
from mofa.agent_build.base.base_agent import MofaAgent, run_agent
import asyncio

logger = logging.getLogger('main')
# 配置日志
logging.basicConfig(
    level=logging.DEBUG,  # 设置日志级别为DEBUG，这样就会输出调试信息
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # 输出到控制台
    ]
)
# c/seven为./目录
project_path = "C:/Users/seven/Desktop/qiAgent/to_mofa/agent-hub/qiAgent/qiagent"
# 更改当前工作目录
os.chdir(project_path)

mcp_server_path = "../mcp_server/mcp_server.py" # 请替换为你的mcp_server.py路径
output_dir = "../../../examples/qiAgent/output"
input_dir = "../../../examples/qiAgent/input"

async def work(pdf_path):
    pdf_path = input_dir + "/" + pdf_path
    # mofa输出中文报错？？？UnicodeEncodeError: 'gbk' codec can't encode character '\u231b' in position 0: illegal multibyte sequence
    # 1.提取pdf简历信息
    logger.log(level=logging.INFO, msg="Start extracting resume information from PDF...")
    pdf_processor = PDFProcessor()
    pdf_content = pdf_processor.extract_text_from_pdf(pdf_path)
    logger.log(level=logging.INFO, msg="Extracted resume information successfully!")

    # 2.获取json化的简历信息
    logger.log(level=logging.INFO, msg="Start obtaining JSON resume information...")
    resumeBot = create_qiBot_from_config(type="resumeBot")
    resume_json = await resumeBot.process_query(pdf_content)
    await resumeBot.close()
    logger.log(level=logging.INFO, msg="Successfully obtained JSON resume information!")

    # 将json化简历信息保存到本地，方便调试
    with open(f"{output_dir}/resume.json", "w", encoding="utf-8") as f:
        f.write(resume_json)
        logger.log(level=logging.INFO, msg=f"Saved JSON resume information to {output_dir}/resume.json")

    # 3.根据简历信息匹配最佳岗位
    logger.log(level=logging.INFO, msg="Start matching the best job positions...")
    matchingBot = create_qiBot_from_config(type="matchingBot")
    await matchingBot.startMCP(mcp_server_path)
    result = await matchingBot.process_query(query=resume_json)
    await matchingBot.close()
    logger.log(level=logging.INFO, msg="Successfully matched the best job positions!")

    # 将匹配结果保存到本地，方便调试
    with open(f"{output_dir}/result.md", "w", encoding="utf-8") as f:
        f.write(result)
        logger.log(level=logging.INFO, msg=f"Saved matching results to {output_dir}/result.md")

    # 4.将md结果转化为pdf
    logger.log(level=logging.INFO, msg="Start converting the results to PDF...")
    pdf_processor = PDFProcessor()
    pdf_processor.md_to_pdf(f"{output_dir}/result.md", f"{output_dir}/result.pdf")
    logger.log(level=logging.INFO, msg=f"PDF result generated successfully! Please check {output_dir}/result.pdf")

    return f"Job recommendation report has been saved to {output_dir}/result.pdf"

@run_agent
def run(agent: MofaAgent):
    file_path = agent.receive_parameter('file_path')
    text = asyncio.run(work(file_path))
    agent.send_output(agent_output_name='text', agent_result=text)

def main():
    agent = MofaAgent(agent_name='qiAgent')
    run(agent)

if __name__ == "__main__":
    main()