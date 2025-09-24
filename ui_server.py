from aiohttp import web
import aiohttp
import asyncio
import json
from qibot import create_qiBot_from_config  # 替换为您的实际模块
messages = []

async def chat_handler(request):
    data = await request.json()
    message = data.get('message', '')
    bot_type = data.get('bot_type', 'qiBot')
    
    # 创建响应对象
    response = web.StreamResponse()
    response.content_type = 'text/plain; charset=utf-8'
    await response.prepare(request)
    
    # 创建agent实例
    agent = create_qiBot_from_config(type=bot_type)
    await agent.startMCP("./mcp_server/mcp_server.py")
    
    # 处理消息（流式输出）
    try:
        # 先发送一个表示开始的信号（可选）
        await response.write("正在思考...\n".encode('utf-8'))
        isthink = True
        # 处理消息流
        async for chunk in agent.process_query_stream(message, isdebug=False):
            if isthink:
                isthink = False
                # 清除“正在思考...”的提示
                await response.write("思考结束，让我来回答你的问题！\n".encode('utf-8'))
            # print(f"Sending chunk: {chunk}")
            await response.write(chunk.encode('utf-8'))
            await asyncio.sleep(0.01)  # 避免发送过快
    except Exception as e:
        print(f"Error during streaming: {e}")
        error_msg = f"\n\n处理错误: {str(e)}"
        await response.write(error_msg.encode('utf-8'))
    finally:
        # 关闭agent
        await agent.close()
        await response.write_eof()
    
    return response

async def tools_handler(request):
    bot_type = request.query.get('bot_type', 'qiBot')
    
    # 创建agent实例
    agent = create_qiBot_from_config(type=bot_type)
    await agent.startMCP("./mcp_server/mcp_server.py")
    
    # 获取可用工具
    tools_response = await agent.mcp_client.session.list_tools()
    tools = [{
        'name': tool.name,
        'description': tool.description
    } for tool in tools_response.tools]
    
    # 关闭agent
    await agent.close()
    
    return web.json_response(tools)

async def history_handler(request):
    # 这里应该从数据库或文件系统中获取用户的聊天历史
    # 简化版：返回空数组
    return web.json_response([])

async def index_handler(request):
    return web.FileResponse('./index.html')

def create_app():
    app = web.Application()
    app.router.add_get('/', index_handler)
    app.router.add_post('/api/chat', chat_handler)
    app.router.add_get('/api/tools', tools_handler)
    app.router.add_get('/api/history', history_handler)
    # app.router.add_static('/static/', path='./static', name='static')
    return app

if __name__ == '__main__':
    app = create_app()
    web.run_app(app, host='localhost', port=8080)