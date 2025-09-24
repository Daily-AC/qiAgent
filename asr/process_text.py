import re

def merge_md_paragraphs(md_text):
    """
    将 Markdown 格式的文本中，段落和列表项整合成一个段落。

    Args:
    md_text: Markdown 格式的字符串。

    Returns:
    整合后的 Markdown 格式的字符串。
    """

    # 使用正则表达式去除列表符号、粗体标记，并移除换行符和多余空格
    cleaned_text = re.sub(r"[*-]", " ", md_text)
    cleaned_text = cleaned_text.replace("\n", " ")
    cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()

    return cleaned_text

if __name__ == "__main__":
    # 示例用法
    md_text = """
    好的，你想听什么类型的歌呢？比如：

    *   **流行歌曲？**
    *   **儿歌？**
    *   **生日歌？**
    *   **随便一首？**

    如果你没有特别想听的，我可以随便唱一首。告诉我你的选择吧！
    """

    merged_text = merge_md_paragraphs(md_text)
    print(merged_text)

    md_text2 = """
    This is the first paragraph.

    - Item 1
    - Item 2

    This is the second paragraph. * Bold Item

    Another paragraph!
    """
    merged_text2 = merge_md_paragraphs(md_text2)
    print(merged_text2)

