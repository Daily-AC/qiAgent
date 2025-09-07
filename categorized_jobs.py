import json
import os
from collections import defaultdict

def classify_json_data(input_file_path, output_dir="classified_data"):
    """
    按照experience和degree对JSON数据进行分类并输出到不同文件
    
    Args:
        input_file_path: 输入的JSON文件路径
        output_dir: 输出目录
    """
    
    # 定义分类标准
    experience_categories = ["经验不限", "在校/应届", "1年以内", "1-3年", "3-5年", "5-10年", "10年以上"]
    degree_categories = ["不限", "本科", "硕士"]
    
    # 创建输出目录
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 读取JSON数据
    try:
        with open(input_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"错误: 找不到文件 {input_file_path}")
        return
    except json.JSONDecodeError:
        print(f"错误: 文件 {input_file_path} 不是有效的JSON格式")
        return
    
    # 如果数据不是列表，转换为列表
    if not isinstance(data, list):
        data = [data]
    
    # 创建分类字典 - 使用嵌套字典存储数据
    classified_data = defaultdict(lambda: defaultdict(list))
    
    # 对每条记录进行分类
    for record in data:
        experience = record.get('experience', '经验不限')
        degree = record.get('degree', '不限')
        
        # 处理经验字段的映射
        if experience not in experience_categories:
            # 如果经验字段不在预定义类别中，尝试映射或设为默认值
            experience = '经验不限'
        
        # 处理学历字段的映射
        if degree not in degree_categories:
            # 如果学历字段不在预定义类别中，尝试映射或设为默认值
            if '博士' in degree or '研究生' in degree:
                degree = '硕士'
            elif '专科' in degree or '大专' in degree:
                degree = '不限'
            else:
                degree = '不限'
        
        # 将记录添加到对应分类中
        classified_data[experience][degree].append(record)
    
    # 生成所有可能的组合文件
    file_count = 0
    for exp in experience_categories:
        for deg in degree_categories:
            # 创建文件名
            filename = f"{exp}_{deg}.json"
            # 替换文件名中的特殊字符
            filename = filename.replace('/', '-').replace('\\', '-').replace(':', '-').replace('*', '-').replace('?', '-').replace('"', '-').replace('<', '-').replace('>', '-').replace('|', '-')
            
            filepath = os.path.join(output_dir, filename)
            
            # 获取该分类的数据
            category_data = classified_data[exp][deg]
            
            # 写入文件（即使是空列表也要创建文件）
            with open(filepath, 'w', encoding='utf-8') as outfile:
                json.dump(category_data, outfile, ensure_ascii=False, indent=2)
            
            file_count += 1
            print(f"创建文件: {filename} - 包含 {len(category_data)} 条记录")
    
    print(f"\n分类完成！总共创建了 {file_count} 个文件")
    
    # 打印统计信息
    print("\n=== 统计信息 ===")
    total_records = sum(len(records) for exp_dict in classified_data.values() for records in exp_dict.values())
    print(f"总记录数: {total_records}")
    
    print("\n按经验分布:")
    for exp in experience_categories:
        count = sum(len(classified_data[exp][deg]) for deg in degree_categories)
        print(f"  {exp}: {count} 条")
    
    print("\n按学历分布:")
    for deg in degree_categories:
        count = sum(len(classified_data[exp][deg]) for exp in experience_categories)
        print(f"  {deg}: {count} 条")

def main():
    """
    主函数 - 使用示例
    """
    # 设置输入文件路径
    input_file = "job_data_city.json"  # 请替换为您的实际文件路径
    
    # 如果文件不存在，创建示例数据
    if not os.path.exists(input_file):
        sample_data = [
            {
                "Idx": "c095752004491203b94d61ad4d97e933",
                "title": "信奥算法C++编程讲师（全国可选）(J10100)",
                "salary": "15-25K",
                "position": "杭州",
                "experience": "经验不限",
                "degree": "本科",
                "tags": "C++,信息学奥赛,信奥教练,C++讲师,CCPC/ICPC",
                "describe": "工作职责:1、按照讲师细则规范组织上课整体流程，负责讲授C++算法编程课程...",
                "company_name": "小码教育",
                "scale": "1000-9999人",
                "industry": "在线教育"
            },
            # 可以添加更多示例数据用于测试
            {
                "Idx": "test001",
                "title": "软件开发工程师",
                "salary": "10-15K",
                "position": "北京",
                "experience": "1-3年",
                "degree": "硕士",
                "tags": "Python,Django,数据库",
                "describe": "负责后端开发工作...",
                "company_name": "测试公司",
                "scale": "100-499人",
                "industry": "互联网"
            }
        ]
        
        with open(input_file, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, ensure_ascii=False, indent=2)
        print(f"创建了示例数据文件: {input_file}")
    
    # 执行分类
    classify_json_data(input_file)

if __name__ == "__main__":
    main()