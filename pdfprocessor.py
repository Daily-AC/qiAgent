import re
import PyPDF2
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont  # 添加TTFont支持
import logging
import os
import pdfkit
from markdown import markdown

class PDFProcessor:
    """PDF处理器"""
    
    @staticmethod
    def extract_text_from_pdf(pdf_path: str) -> str:
        """从PDF中提取文本"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                
                if not text.strip():
                    raise ValueError("PDF文件为空或无法提取文本")
                
                return text
        except Exception as e:
            # logger.error(f"PDF文本提取失败: {e}")
            print(f"😡PDF文本提取失败: {e}")
            raise



    def md_to_pdf(self, input_md: str, output_pdf: str):
        """
        将 Markdown 文件转换为 PDF 文件，支持数学公式和中文显示。
        
        依赖:
        - pdfkit: 用于将 HTML 转换为 PDF
        - markdown: 用于将 Markdown 转换为 HTML
        - wkhtmltopdf: 需要安装并配置环境变量，下载地址 https://wkhtmltopdf.org/downloads.html
        
        参数:
        - input_md: 输入的 Markdown 文件路径
        - output_pdf: 输出的 PDF 文件路径
        """
        # 1. 读取 Markdown 文件
        with open(input_md, 'r', encoding='utf-8') as f:
            md_text = f.read() 

        with open(input_md, 'r', encoding='utf-8') as f:
            md_text = f.read()

        # 2. 将 Markdown 转换为 HTML
        #    使用 'tables' 扩展防止表格转换混乱:cite[2]
        #    使用 'mdx_math' 扩展处理数学公式:cite[2]
        html_content = markdown(md_text, output_format='html', extensions=['tables', 'mdx_math'])

        # 3. 构建完整的 HTML 文档结构，并添加 KaTeX 支持以渲染数学公式
        #    注意：wkhtmltopdf 对现代 CSS 和 JavaScript 的支持有限，复杂公式可能仍需调整
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <!-- 引入 KaTeX 样式和脚本以渲染数学公式 -->
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex/dist/katex.min.css" crossorigin="anonymous">
            <script src="https://cdn.jsdelivr.net/npm/katex/dist/katex.min.js" crossorigin="anonymous"></script>
            <script src="https://cdn.jsdelivr.net/npm/katex/dist/contrib/mathtex-script-type.min.js" defer></script>
            <!-- 指定中文字体以确保中文正确显示 -->
            <style>
                body {{
                    font-family: "SimSun", "Microsoft YaHei", sans-serif; /* 设置中文字体栈 */
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """

        # 4. 配置 pdfkit
        #    指定 wkhtmltopdf 的安装路径（如果已添加到系统 PATH，可以设为 None）
        #    对于 Windows，可能需要类似 r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe' 的路径
        config = pdfkit.configuration(wkhtmltopdf='./wkhtmltox/bin/wkhtmltopdf.exe')  # 根据你的实际路径修改

        # 5. 将 HTML 转换为 PDF
        #    可以添加更多选项，如页边距等
        pdfkit.from_string(full_html, output_pdf, configuration=config, options={'encoding': "UTF-8"})


