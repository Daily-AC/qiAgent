from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import sys
from contextlib import AsyncExitStack
from typing import Optional
import os
from openai import AsyncOpenAI, OpenAI
import asyncio
import json
import logging
import yaml
from pathlib import Path
import time

class MCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.enabled = False
        
    async def connect_to_server(self, server_script_path: str):
        server_params = StdioServerParameters(
            command="python",
            args=[server_script_path],
            env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()
        self.enabled = True
        # 列出可用工具
        response = await self.session.list_tools()
        tools = response.tools
        print("\n😄连接到MCP Server，工具如下:", [tool.name for tool in tools])
    async def close(self):
        """显式关闭所有资源"""
        await self.exit_stack.aclose()
        self.enabled = False
        print("😎MCP client closed.")

class qiBot:
    def __init__(self, base_url: str, api_key_list: list, model: str, max_tokens: int = 2048, system_prompt: str = ""):
        self.client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key_list[0],
        )
        self.api_key_list = api_key_list
        self.model = model
        self.max_tokens = max_tokens
        self.mcp_client = MCPClient()
        self.system_prompt = system_prompt

    async def startMCP(self, server_script_path: str):
        try:
            await self.mcp_client.connect_to_server(server_script_path)
            print("😎MCP server started and connected.")
            # logging.info("MCP server started and connected.")
        except Exception as e:
            print(f"😡Error starting MCP: {e}")
            # logging.error(f"Error starting MCP: {e}")

    async def process_query(self, query: str, _messages: list = None, isstream: bool = False, isdebug: bool = False) -> str:
        """使用 LLM 和 MCP 服务器提供的工具处理查询(单轮)"""
        """
            流式输出还是有问题，可能不同的平台对于响应的json解析程度不同，一旦是坏的
            就会导致整个流式输出失败，也会导致后面调用工具受影响
        """
        if _messages:
            messages = _messages
        else:
            messages = [
                {
                    "role": "system",
                    "content": self.system_prompt
                }
            ]
        messages.append(
            {
                "role": "user",
                "content": query
            }
        )
        # def is_valid_json(json_str):
        #     try:
        #         json.loads(json_str)
        #         return True
        #     except json.JSONDecodeError:
        #         return False
        available_tools = []
        if self.mcp_client.enabled:
            response = await self.mcp_client.session.list_tools()
            available_tools = [{
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            } for tool in response.tools]
        key_index = 0
        self.client.api_key = self.api_key_list[key_index]
        if isdebug: print(f"\033[32m Using {key_index} API Key: {self.client.api_key} \033[0m")
        key_index = (key_index + 1) % len(self.api_key_list)
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=available_tools,
            max_tokens=self.max_tokens,
            stream=isstream
        )


        final_text = []
        curr_content = ""
        curr_tools = []
        if isstream:
            async for chunk in response:
                chunk_message = chunk.choices[0].delta
                if chunk_message.tool_calls:
                    for tool_call in chunk_message.tool_calls:
                        curr_tools.append(tool_call)
                if chunk_message.content:
                    curr_content += chunk_message.content
                    print(chunk_message.content, end="", flush=True)
            if curr_content: print()
            print(f"\033[32m done \033[0m")
        else:
            curr_content = response.choices[0].message.content
            if curr_content and isdebug: print(f"\033[32m {curr_content} \033[0m")
            curr_tools = response.choices[0].message.tool_calls
        
        if curr_content:
            final_text.append(curr_content)
            messages.append({
                "role": "assistant",
                "content": curr_content
            })
            

        # 处理响应并处理工具调用
        while curr_tools:
            # 处理每个工具调用
            for tool_call in curr_tools:
                tool_name = tool_call.function.name
                try:
                    tool_args = json.loads(tool_call.function.arguments)
                except Exception as e:
                    print(f"\033[31m fuck \033[0m")
                    continue
                # 执行工具调用
                result = await self.mcp_client.session.call_tool(tool_name, tool_args)
                # final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")
                print(f"👿[正在使用工具 {tool_name} 及其参数 {tool_args}]")
                # 将工具调用和结果添加到消息历史
                messages.append({
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": json.dumps(tool_args)
                            }
                        }
                    ]
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result.content)
                })

            messages.append({
                "role": "user",
                "content": "继续"
            })
            is_ok = False
            while not is_ok:
                time.sleep(1)  # 避免过快调用

                self.client.api_key = self.api_key_list[key_index]
                if isdebug: print(f"\033[32m Using {key_index} API Key: {self.client.api_key} \033[0m")
                key_index = (key_index + 1) % len(self.api_key_list)
                try:
                    response = await self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        tools=available_tools,
                        max_tokens=self.max_tokens,
                        stream=isstream,
                    )
                    print(f"❤️‍🔥[没有429！]")
                    is_ok = True
                except Exception as e:
                    response = e
                    print(f"😡Error during LLM call: {e}")
                    time.sleep(2)
                # INFO:httpx:HTTP Request: POST https://api.moonshot.cn/v1/chat/completions "HTTP/1.1 429 Too Many Requests"
                

            curr_tools = []
            curr_content = ""

            if isstream:
                async for chunk in response:
                    chunk_message = chunk.choices[0].delta
                    if chunk_message.tool_calls:
                        for tool_call in chunk_message.tool_calls:
                            curr_tools.append(tool_call)
                    if chunk_message.content:
                        curr_content += chunk_message.content
                        print(chunk_message.content, end="", flush=True)
                if curr_content: print()
                # 输出；绿色的
                print(f"\033[32m done \033[0m")
            else:
                curr_content = response.choices[0].message.content
                if curr_content and isdebug: print(f"\033[32m {curr_content} \033[0m")
                curr_tools = response.choices[0].message.tool_calls

            if curr_content:
                final_text.append(curr_content)
                messages.append({
                    "role": "assistant",
                    "content": curr_content
                })
                

        return "\n".join(final_text)
    
    async def chat_loop(self, ismulti: bool = False, isstream: bool = False):
        """启动一个交互式聊天循环(多次单轮)"""
        print("Entering chat loop. Type 'exit' to quit.")
        messages = [
            {
                "role": "system",
                "content": self.system_prompt
            }
        ]
        if not ismulti:
            messages = None
        
        while True:
            try:
                user_input = input("\033[1;36m King \033[0m: ")
                if user_input.lower() in ["exit", "quit"]:
                    print("Exiting chat loop.")
                    break
                print("\033[1;33m qiBot \033[0m: ", end="")
                await self.process_query(user_input, messages, isstream, isdebug=True)
            except Exception as e:
                logging.error(f"Error in chat loop: {e}")
    async def close(self):
        """清理资源"""
        if self.mcp_client.enabled:
            await self.mcp_client.close()



class qiBotConfig:
    def __init__(self, config_path="config.yml", type="qiBot"):
        self.config_path = Path(config_path)
        self.config = self.load_config()
        self.type = type
    
    def load_config(self):
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件 {self.config_path} 不存在")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def get_qiBot_config(self):
        return self.config.get(self.type, {})

def create_qiBot_from_config(config_path="config.yml", type="qiBot"):
    config_loader = qiBotConfig(config_path, type)
    config = config_loader.get_qiBot_config()
    
    return qiBot(
        config.get('api_base'),
        config.get('api_key_list'),
        config.get('model'),
        config.get('max_tokens'),
        config.get('system_message')
    )

async def main():
    """主函数"""
    agent = create_qiBot_from_config(type="matchingBot")
    try:
        await agent.startMCP("./mcp_server/mcp_server.py") # 是否调用工具
        await agent.chat_loop(True, False)
    finally:
        await agent.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())