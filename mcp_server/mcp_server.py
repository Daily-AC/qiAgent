from fastmcp import FastMCP
from datetime import datetime
import os

mcp = FastMCP()

@mcp.tool
def get_current_time():
    """Get current time"""
    return datetime.now()
@mcp.tool
def show_info():
    """Show info"""
    return """
    This is a local data visit example using FastMCP.
    You can access local data and perform operations using the defined tools.
    author: e0_7
    """
@mcp.tool
def list_files():
    """列出classified_data目录下的所有文件并返回字符串"""
    result = []
    result.append("当前目录下的所有文件:")
    result.append("-" * 40)
    
    current_dir = "./classified_data"

    # 列出所有文件和目录
    all_items = os.listdir(current_dir)
    
    # 过滤出文件（排除目录）
    files = [item for item in all_items if os.path.isfile(os.path.join(current_dir, item))]
    
    if not files:
        result.append("当前目录下没有文件")
        return "\n".join(result)
    
    # 按字母顺序排序
    files.sort()
    
    # 构建文件列表字符串
    for i, file in enumerate(files, 1):
        file_size = os.path.getsize(os.path.join(current_dir, file))
        result.append(f"{i:2d}. {file} ({file_size} bytes)")
    
    return "\n".join(result)

@mcp.tool
def read_file(filename):
    """查看classified_data目录下指定文件的内容并返回字符串"""
    filename = "./classified_data/" + filename
    result = []
    try:
        # 检查文件是否存在
        if not os.path.exists(filename):
            return f"错误: 文件 '{filename}' 不存在"
        
        # 检查是否为文件
        if not os.path.isfile(filename):
            return f"错误: '{filename}' 不是一个文件"
        
        # 获取文件大小
        file_size = os.path.getsize(filename)
        
        result.append(f"文件 '{filename}' 的内容 ({file_size} bytes):")
        result.append("-" * 50)
        
        # 读取并返回文件内容
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read()
            result.append(content)
            
        return "\n".join(result)
            
    except UnicodeDecodeError:
        return "无法以文本形式读取文件（可能是二进制文件）"
    except PermissionError:
        return f"错误: 没有读取文件 '{filename}' 的权限"
    except Exception as e:
        return f"读取文件时发生错误: {e}"
def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()