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
