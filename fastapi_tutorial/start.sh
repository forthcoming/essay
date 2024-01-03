# main: main.py文件
# app: 在main.py文件中通过app = FastAPI()创建的对象
# --reload: 让服务器在更新代码后自动重启,仅在开发时使用该选项
uvicorn main:app --reload --host 127.0.0.1 --port 8000
