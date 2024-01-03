import uvicorn
from fastapi import FastAPI, Query, Path, Body, status, Response, HTTPException
from pydantic import BaseModel, Field, HttpUrl

'''
POST: 创建数据
GET: 读取数据
PUT: 更新数据
DELETE: 删除数据
'''

app = FastAPI()


class Item(BaseModel):
    name: str  # 没有默认值为必填字段
    price: float = Field(gt=0, description="The price must be greater than zero")
    is_offer: bool | None = Field(default=True)
    url: HttpUrl  # 检查是否为有效的URL,并在JSON Schema / OpenAPI文档中进行记录


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


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)
