import time
import uvicorn
import pyaudio
import requests
from fastapi import FastAPI, Query, Path, Body, status, Response, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, HttpUrl
from python.redis_cache import rc

'''
POST: 创建数据
GET: 读取数据
PUT: 更新数据
DELETE: 删除数据

请求头举例:
Accept-Encoding:
Accept-Language:
Cookie:
Host:
Referer:
User-Agent:

响应头举例:
Content-Encoding:
Content-Length:
Content-Type:
Keep-Alive:
Access-Control-Allow-Origin:
Access-Control-Allow-Methods:
'''


class Item(BaseModel):
    name: str  # 没有默认值为必填字段
    price: float = Field(gt=0, description="The price must be greater than zero")
    is_offer: bool | None = Field(default=True)
    url: HttpUrl  # 检查是否为有效的URL,并在JSON Schema / OpenAPI文档中进行记录


class StreamingInputs(BaseModel):
    cid: int


app = FastAPI(
    title="TTS Streaming server",
    docs_url="/",
)

# refer: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/CORS
# refer: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Headers/Access-Control-Allow-Credentials
# 跨域资源共享(CORS)是一种机制,它使用额外的HTTP头来告诉浏览器,让运行的Web应用被准许访问来自不同源服务器上的指定的资源
# 当一个资源从与该资源本身所在的服务器不同的域、协议或端口请求一个资源时,资源会发起一个跨域HTTP请求
# 浏览器先往目标url发起OPTIONS请求,根据服务端返回的Allow-Origin等信息判断是否继续进行跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:8080", "https://localhost"],  # 允许跨域请求的源列表
    allow_credentials=True,  # 指示跨域请求是否支持cookies
    allow_methods=["*"],  # POST,PUT等,通配符 "*" 允许所有方法
    allow_headers=["*"],
    max_age=600,  # 设定浏览器缓存CORS响应的最长时间,单位是秒,默认为600
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    # 请求前
    response = await call_next(request)
    # 响应后
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.get('/items/{item_id}')  # 路径参数item_id的值将作为参数item_id传递给你的函数
async def read_item(
        response: Response,
        item_id: int = Path(ge=1),
        q: str | None = Query(default=None, max_length=50, pattern=r"^fixed"),
):
    # item_id被申明为int,当访问127.0.0.1:8000/items/foo时,会看到一个清晰可读的HTTP错误
    # 声明不属于路径参数的其他函数参数时,它们将被自动解释为"查询字符串"参数(如这里的参数q),url可通过?q=xxx形式传参,如果不给q默认值则为必传参数
    # 当定义q: list[str]时,可通过localhost:8000/items/?q=foo&q=bar方式接受查询参数
    response.headers["X-Cat-Dog"] = "alone in the world"
    response.set_cookie(key="fake", value="fake-cookie-session-value")
    response.status_code = status.HTTP_202_ACCEPTED
    if item_id > 10:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="item_id too big")
    return {'item_id': item_id, 'q': q}


@app.post("/items/", tags=['modify'], summary="创建一个item")
async def create_item(item: Item, importance: int = Body(default=5)):  # item为请求体
    """
    Create an item with all the information:
    - **name**: each item must have a name
    - **price**: required
    """
    # importance默认为Query查询参数类型,Body的意思在同一请求体中具有另一个键importance
    # FastAPI期望如下形式的请求体:
    # {
    #   "item": {
    #     "name": "string",
    #     "price": 0,
    #     "is_offer": true
    #   },
    #   "importance": 5
    # }
    return item, importance


@app.put("/items/{item_id}", status_code=status.HTTP_201_CREATED, tags=['modify'])
def update_item(item_id: int, item: Item) -> dict[str, int | str]:  # 定义的返回值类型会体现在docs接口文档中
    return {"item_name": item.name, "item_id": item_id}


def predict_streaming_generator(inputs):
    while True:
        cache = rc.blpop(f'audio_stream:tts_audio_queue:{inputs.cid}', 0)[1]
        yield cache


@app.post("/tts_stream")
def predict_streaming_endpoint(inputs: StreamingInputs):
    return StreamingResponse(
        predict_streaming_generator(inputs),
        media_type="audio/wav",
    )


def receive_tts():
    player = pyaudio.PyAudio()
    stream = player.open(format=player.get_format_from_width(2), channels=1, rate=16000, output=True)
    with requests.post(
            f"http://localhost:8000/tts_stream",
            json={'cid': 1},
            stream=True,
    ) as f:
        for chunk in f.iter_content(chunk_size=512):  # 数据不够chunk_size大小时会被阻塞
            stream.write(chunk)
    # 本应用以下代码执行不到,应为服务端是死循环
    stream.stop_stream()
    stream.close()
    player.terminate()


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)
    # uvicorn main:app --reload --host 0.0.0.0 --port 8000
