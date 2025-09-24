'''
jobs info json to text for building knowledge base
'''

import json

def process_json_to_text(input_file, output_file):
    # 读取JSON文件
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 准备输出文本
    output_lines = []
    
    for idx, item in enumerate(data):
        # 构建每个职位的描述文本
        text_parts = [
            f"这里有一份{item.get('title', '未知职位')}的工作机会，",
            f"工作地点位于{item.get('position', '未知地点')}，",
            f"提供的薪资范围是{item.get('salary', '面议')}。",
            f"要求有{item.get('experience', '不限')}的工作经验，",
            f"学历要求为{item.get('degree', '不限')}。",
            f"需要掌握的技能包括：{item.get('tags', '无')}。",
            f"具体职责描述如下：{item.get('describe', '暂无描述')}",
            f"公司名称是{item.get('company_name', '未知公司')}，",
            f"公司规模为{item.get('scale', '未知规模')}，",
            f"属于{item.get('industry', '未知行业')}行业。"
        ]
        
        # 连接所有部分，并添加结尾符
        combined_text = ' '.join(text_parts) + '(qi)'
        output_lines.append(combined_text)
    
    # 写入输出文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))

if __name__ == "__main__":
    # 使用示例
    process_json_to_text('job_data_city.json', 'output.txt')