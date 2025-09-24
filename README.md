# qiAgent---求职求知

## 项目简介

qiAgent 是一个一站式求职助手。它能够自动提取 PDF 简历内容，结构化为 JSON 格式，并通过智能匹配算法为候选人推荐最合适的岗位。最终结果支持导出为 Markdown 和 PDF 格式，方便查看与分享；支持求职者针对求职问题深度对话以及AI模拟面试。

## 主要功能

- PDF 简历文本提取
- 简历内容结构化（JSON 格式）
- 岗位智能匹配
- 匹配结果导出为 Markdown 和 PDF
- 日志记录与调试支持
- web端深度对话
- AI模拟面试

## 目录结构

```
.
├── categorized_jobs.py        # 岗位分类脚本
├── config.yml                 # 配置文件
├── job_data_city.json         # 城市岗位数据
├── main.py                    # 主程序入口
├── pdfprocessor.py            # PDF 处理模块
├── qibot.py                   # 智能 Bot 逻辑
├── to_mcp.py                  # 项目MCP化
├── test.py                    # 测试脚本
├── output/                    # 输出目录（结果、简历 JSON 等）
├── resume/                    # 存放简历 PDF
├── classified_data/           # 分类后的岗位数据
├── mcp_server/                # MCP 服务端
├── asr/                       # 语音模块
└── to_mofa/                   # mofa实现版本
```

## 视频演示

原项目演示：

[<video src="./video/原项目.mp4"></video>](https://github.com/user-attachments/assets/c689e93d-2fa7-4d2b-bf02-b32b8902a331)

mofa化演示：

[<video src="./video/mofa化.mp4"></video>](https://github.com/user-attachments/assets/fd8ba870-35bb-4b90-8d36-39d98b401cef)

mcp化演示：

[<video src="./video/mcp化.mp4"></video>](https://github.com/user-attachments/assets/d20bd9f4-f9ab-4383-a4c5-ab0244520c2a)

## 快速开始

注意：截至目前，本项目仅在win11系统进行过测试

### 0.拉取项目

```powershell
# 克隆本项目
git clone https://github.com/Daily-AC/qiAgent.git

# 进入项目目录
cd qiAgent
```

### 1. uv环境

```powershell
# 使用powershell安装
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 验证安装
uv --version

# 为项目创建虚拟环境
uv venv --python 3.11
```

### 2. 安装依赖

```bash
# 根据uv.lock安装相关依赖 建议开代理
uv sync
```

由于需要md转pdf，所以需要额外安装[wkhtmltox](https://wkhtmltopdf.org/downloads.html)至项目根目录的wkhtmltox文件夹下。为防止大家搞错，说明一下最后完成后exe的路径应为 =="./wkhtmltox/bin/wkhtmltopdf.exe"==


### 3. 配置API KEY

 - 打开config.yml填写所有的base_url和api_key_list，对应模型需支持Openai格式的API。
 - 打开asr/tts.py填写APP_ID、API_KEY和SECRET_KEY。

### 4. 准备简历文件

将你的简历 PDF 文件放入 `./resume/` 目录，并命名为 `resume.pdf`（或在 `main.py` 中修改路径）。

### 5. 运行主程序

```bash
uv run main.py
```

### 6. 查看结果

- 结构化简历信息：`./output/resume.json`
- 匹配岗位结果（Markdown）：`./output/result.md`
- 匹配岗位结果（PDF）：`./output/result.pdf`

## 主要模块说明

- `pdfprocessor.py`：负责 PDF 文本提取与 Markdown 转 PDF。
- `qibot.py`：支持调用MCP Tools、多轮对话的agent，可实现简历解析与岗位匹配智能 Bot。
- `asrbot.py`: AI模拟面试Bot。
- `mcp_server/mcp_server.py`：stdio式的MCP Server，支持查看指定目录的文件列表及内容。
- `classified_data/`：岗位分类数据，支持多种学历与经验组合。

## 配置说明

- `config.yml`：Bot 及服务相关配置。
- `job_data_city.json`：岗位与城市数据。

## 项目MCP化测试

```shell
uv run to_mcp.py # 开启streamableHttp类型的MCP Server
```

接着打开cherry studio配置：

 - 类型选择streamableHttp
 - URL填写：http://localhost:8000/mcp
 - 打开长时间运行模式
 - 超时设置为360
 - 保存打开即可

关于使用：
 - 告诉LLM相对本项目根目录的相对地址即可。
 - 输出产物在output文件夹里。

## moly调用

将下方json代码粘贴到moly的MCP中

```json
{
  "servers": {
    "test": {
      "url": "http://localhost:8000/mcp",
      "type": "streamable-http"
    }
  }
}
```
![moly调用MCP](./img/moly调用.png)

使用方法同cherry studio，上图调用成功！

## mofa化的项目

 - 在./to_mofa/examples/qiAgent/readme.md
 - 暂时存在的问题：mofa-ai包会跟原项目所依赖的库发生冲突，待解决。mofa化的项目暂时不可用~

## 多轮对话（可调用MCP Tools）

```shell
uv run qibot.py # 测试
```

在里面可以实现多轮对话，可以选择是否使用MCP工具，详见代码末尾。

```
agent = create_qiBot_from_config(type="matchingBot")
```

在上述代码中可以修改agent的角色：
 - qiBot：日常化Bot
 - resumeBot：简历结构化Bot
 - matchingBot：岗位匹配与建议Bot
 - interviewBot：面试建议与模拟Bot

## 多轮对话+前端UI（可以根据简历岗位问题进行畅聊）

```
# 开启web服务
uv run ui_server.py

# 随后打开localhost:8080进行使用
```

## AI模拟面试

```
# 流程：speech to text -> interviewBot -> text to speech
uv run asrbot.py
```

## ToDo:
 - 解决MoFA包冲突问题
 - 找到发展方向，提升创新点（hard）
 - 继续开发多模态，升级AI模拟面试为实时语音流
 - 尝试微调bot替换提示词工程（hard）
 - 继续构建知识库以及思考初筛策略
 - 思考更深刻的匹配算法
  
## 思考
切实提升自我价值、自身能力以适应这瞬息万变的时代！
切莫贪多，专注于一件事，做成功一件事，脚踏实地，来日方长！
