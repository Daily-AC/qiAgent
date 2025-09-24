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

def debug(msg: str, isdebug: bool = False, end: str = "\n", flush: bool = False):
    if isdebug:
        print(f"\033[33m[DEBUG] {msg}\033[0m", end=end, flush=flush)


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

    async def process_query(self, query: str, _messages: list = None, isstream: bool = False, isdebug: bool = False):
        """使用 LLM 和 MCP 服务器提供的工具处理查询"""
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
        debug(f" Using {key_index} API Key: {self.client.api_key} ", isdebug)
        key_index = (key_index + 1) % len(self.api_key_list)
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=available_tools,
            max_tokens=self.max_tokens,
            stream=isstream
        )
        # print(response)

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
                    print(f"\033[32m{chunk_message.content}\033[0m", end="", flush=True)
                    # yield chunk_message.content
            if curr_content: print("")
            debug(f"✅ \033[32m done \033[0m", isdebug=isdebug)
        else:
            curr_content = response.choices[0].message.content
            if curr_content: print(f"\033[32m{curr_content}\033[0m")
            curr_tools = response.choices[0].message.tool_calls
        
        if curr_content:
            final_text.append(curr_content)
            messages.append({
                "role": "assistant",
                "content": curr_content
            })

        debug(f"👿[工具调用列表: {curr_tools}]", isdebug=isdebug)

        # 处理响应并处理工具调用
        while curr_tools:
            # 处理每个工具调用
            for tool_call in curr_tools:
                tool_name = tool_call.function.name
                if not tool_name:
                    debug(f"❌ \033[31m Tool name is missing in tool call {tool_call} \033[0m", isdebug=isdebug)
                    continue
                try:
                    # tool_call.function.arguments
                    # debug(f"👿[工具调用: {tool_name}, 参数: {tool_call.function.arguments}]", isdebug=isdebug)
                    # 如果tool_call.function.arguments没有被{}包裹，则补全
                    if not tool_call.function.arguments.startswith("{"):
                        tool_call.function.arguments = "{" + tool_call.function.arguments + "}"
                    tool_args = json.loads(tool_call.function.arguments)
                except Exception as e:
                    debug(f"❌ \033[31m fuck \033[0m", isdebug=isdebug)
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
                debug(f" Using {key_index} API Key: {self.client.api_key} ", isdebug)
                key_index = (key_index + 1) % len(self.api_key_list)
                try:
                    response = await self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        tools=available_tools,
                        max_tokens=self.max_tokens,
                        stream=isstream,
                    )
                    # print(response)
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
                        print(f"\033[32m{chunk_message.content}\033[0m", end="", flush=True)
                        # yield chunk_message.content
                if curr_content: print("")
                debug(f"✅ \033[32m done \033[0m", isdebug=isdebug)
            else:
                curr_content = response.choices[0].message.content
                if curr_content: print(f"\033[32m{curr_content}\033[0m")
                curr_tools = response.choices[0].message.tool_calls

            if curr_content:
                final_text.append(curr_content)
                messages.append({
                    "role": "assistant",
                    "content": curr_content
                })
                

        return "\n".join(final_text)
    
    async def process_query_stream(self, query: str, _messages: list = None, isdebug: bool = False):
        """使用 LLM 和 MCP 服务器提供的工具处理查询"""
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
        debug(f" Using {key_index} API Key: {self.client.api_key} ", isdebug)
        key_index = (key_index + 1) % len(self.api_key_list)
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=available_tools,
            max_tokens=self.max_tokens,
            stream=True
        )

        final_text = []
        curr_content = ""
        curr_tools = []
        async for chunk in response:
            chunk_message = chunk.choices[0].delta
            if chunk_message.tool_calls:
                for tool_call in chunk_message.tool_calls:
                    curr_tools.append(tool_call)
            if chunk_message.content:
                curr_content += chunk_message.content
                print(f"\033[32m{chunk_message.content}\033[0m", end="", flush=True)
                yield chunk_message.content
        if curr_content:
            print("")
            yield "\n"

        debug(f"✅ \033[32m done \033[0m", isdebug=isdebug)
        
        if curr_content:
            final_text.append(curr_content)
            messages.append({
                "role": "assistant",
                "content": curr_content
            })

        debug(f"👿[工具调用列表: {curr_tools}]", isdebug=isdebug)

        # 处理响应并处理工具调用
        while curr_tools:
            # 处理每个工具调用
            for tool_call in curr_tools:
                tool_name = tool_call.function.name
                if not tool_name:
                    debug(f"❌ \033[31m Tool name is missing in tool call {tool_call} \033[0m", isdebug=isdebug)
                    continue
                try:
                    # tool_call.function.arguments
                    # debug(f"👿[工具调用: {tool_name}, 参数: {tool_call.function.arguments}]", isdebug=isdebug)
                    # 如果tool_call.function.arguments没有被{}包裹，则补全
                    if not tool_call.function.arguments.startswith("{"):
                        tool_call.function.arguments = "{" + tool_call.function.arguments + "}"
                    tool_args = json.loads(tool_call.function.arguments)
                except Exception as e:
                    debug(f"❌ \033[31m fuck \033[0m", isdebug=isdebug)
                    continue
                # 执行工具调用
                result = await self.mcp_client.session.call_tool(tool_name, tool_args)
                # final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")
                yield f"👿[正在使用工具 {tool_name} 及其参数 {tool_args}]\n"
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
                debug(f" Using {key_index} API Key: {self.client.api_key} ", isdebug)
                key_index = (key_index + 1) % len(self.api_key_list)
                try:
                    response = await self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        tools=available_tools,
                        max_tokens=self.max_tokens,
                        stream=True,
                    )
                    # print(response)
                    print(f"❤️‍🔥[没有429！]")
                    is_ok = True
                except Exception as e:
                    response = e
                    print(f"😡Error during LLM call: {e}")
                    time.sleep(2)
                # INFO:httpx:HTTP Request: POST https://api.moonshot.cn/v1/chat/completions "HTTP/1.1 429 Too Many Requests"
                

            curr_tools = []
            curr_content = ""


            async for chunk in response:
                chunk_message = chunk.choices[0].delta
                if chunk_message.tool_calls:
                    for tool_call in chunk_message.tool_calls:
                        curr_tools.append(tool_call)
                if chunk_message.content:
                    curr_content += chunk_message.content
                    print(f"\033[32m{chunk_message.content}\033[0m", end="", flush=True)
                    yield chunk_message.content
            if curr_content:
                print("")
                yield "\n"

            debug(f"✅ \033[32m done \033[0m", isdebug=isdebug)
            
            if curr_content:
                final_text.append(curr_content)
                messages.append({
                    "role": "assistant",
                    "content": curr_content
                })
        yield "\n\n"
    
    async def chat_loop(self, ismulti: bool = False, isstream: bool = False, isdebug: bool = False):
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
                if not user_input.strip():
                    continue
                if user_input.lower() in ["exit", "quit"]:
                    print("Exiting chat loop.")
                    break
                print("\033[1;33m qiBot \033[0m: ", end="")
                await self.process_query(user_input, messages, isstream, isdebug=isdebug)
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
    agent = create_qiBot_from_config(type="qiBot")
    try:
        await agent.startMCP("./mcp_server/mcp_server.py") # 是否调用工具
        await agent.chat_loop(True, True, True)  # 多轮，流式，调试
    except Exception as e:
        logging.error(f"Error in main: {e}")
    finally:
        await agent.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

'''
if isstream:
    async for chunk in response:
        chunk_message = chunk.choices[0].delta
        if chunk_message.tool_calls:
            for tool_call in chunk_message.tool_calls:
                curr_tools.append(tool_call)
        if chunk_message.content:
            curr_content += chunk_message.content
            # green
            debug(f"\033[32m {chunk_message.content} \033[0m", isdebug=isdebug, end="", flush=True)
    if curr_content: debug("", isdebug=isdebug)
    debug(f"✅ \033[32m done \033[0m", isdebug=isdebug)
else:
    curr_content = response.choices[0].message.content
    if curr_content: debug(f"\033[32m {curr_content} \033[0m", isdebug=isdebug)
    curr_tools = response.choices[0].message.tool_calls

[DEBUG] 👿[工具调用列表: [ChatCompletionMessageToolCall(id='get_current_time:0', function=Function(arguments='{}', name='get_current_time'), type='function', index=0)]]
[DEBUG] 👿[工具调用列表: [ChoiceDeltaToolCall(index=0, id='get_current_time:0', function=ChoiceDeltaToolCallFunction(arguments='', name='get_current_time'), type='function'), ChoiceDeltaToolCall(index=0, id=None, function=ChoiceDeltaToolCallFunction(arguments='{}', name=None), type=None)]]
'''