import httpx
from fastapi import FastAPI, Request
from starlette.responses import StreamingResponse
import uvicorn
import json
from loguru import logger

logger.add("llm.log", level="INFO", enqueue=True)  # 写入文件
app = FastAPI(title="LLM API Logger")


async def event_stream(request, body):
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream(
                method="POST",
                url="https://openrouter.ai/api/v1/chat/completions",
                json=body,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream",
                    "Authorization": request.headers.get("Authorization"),
                },
        ) as response:
            async for line in response.aiter_lines():
                logger.info(line)
                yield f"{line}\n"


@app.post("/chat/completions")
async def proxy_request(request: Request):
    body = await request.json()
    logger.info(f"{json.dumps(body, ensure_ascii=False)}")
    return StreamingResponse(event_stream(request, body), media_type="text/event-stream")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    # nginx也可以做类似的转发操作,但没法详细的记录日志,无法很好的支持流式响应转发
    # cline配置:
    # 打开设置,API Provide选择OpenAI Compatible, Base URL填写http://localhost:8000,API Key填写OpenRouter的key,就可以使用了

    # cline在传递工具时,是把工具的描述,通过messages传给了模型
    # 如果模型要使用工具,提示词会让模型以特定的格式作为内容返回
    # 所以就可以避免各种模型不兼容的问题
    # 使用get_flight_info获取航班信息,模型就返回一下内容
    # <use_mcp_tool>
    # <server_name>local/tour</server_name>
    # <tool_name>get_flight_info</tool_name>
    # <arguments>
    # {
    #   "date": "2025-04-01",
    #   "origin": "深圳"
    # }
    # </arguments>
    # </use_mcp_tool>

    # <ask_followup_question> </ask_followup_question> 模型询问用户问题(比如模型不知道接下来做什么,或者用户的问题不清晰)
    # <thinking> </thinking> 模型思考用户的提问,模型回答结束前也会思考
    # <attempt_completion> </attempt_completion> 标志着模型回答结束

# ReAct（Reasoning and Acting）是一种结合“语言推理”和“工具行动”的智能体（Agent）决策模式，用于提升语言模型在复杂任务中的表现
# ReAct模式使得语言模型不仅能思考和规划,还可以交互和执行,并在执行后继续思考下一步
# 可以设置模型开头提示词: 你是一个智能助手，遵循 ReAct 模式推理
# cline就是使用ReAct模式的智能体,类似的还有Chain-of-Thought模式

# ReAct模式引入了以下三个关键组成部分：
# Thought(思考): 语言模型描述它的当前推理
# Action(行动): 模型选择一个工具,并传入参数调用
# Observation(观察): 系统返回工具调用的结果,供下一步思考使用
# 这个过程会循环多轮,直到模型给出最终的答案
