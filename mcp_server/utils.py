def parse_job_file(filename):
    """
    将job文件解析为字典格式
    """
    job_dict = {}
    
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # 按序列号分割内容
        entries = content.split('序列号：')
        
        for entry in entries[1:]:  # 跳过第一个空元素
            if entry.strip():
                # 提取序列号
                serial_number = entry.split('。')[0].strip()
                # 整个字符串作为值
                full_text = '序列号：' + entry.strip()
                job_dict[serial_number] = full_text
                
        return job_dict
        
    except FileNotFoundError:
        print(f"错误：找不到文件 {filename}")
        return {}
    except Exception as e:
        print(f"读取文件时出错：{e}")
        return {}
JOB_INFO_DICT = {}
def init_job_info_dict():
    global JOB_INFO_DICT
    JOB_INFO_DICT = parse_job_file("output.txt")
    
# 使用示例
if __name__ == "__main__":
    # 解析文件
    jobs = parse_job_file("output.txt")
    
    
    
    print(f"成功解析了 {len(jobs)} 个工作机会")