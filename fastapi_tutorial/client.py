import requests
import pyaudio


def test_get_items():
    r = requests.get('http://127.0.0.1:8000/items/9?q=fixed_you')
    print(r.json())
    print(r.headers)
    print(r.status_code)  # 202


def test_post_items():
    r = requests.post(
        url='http://127.0.0.1:8000/items',
        json={
            "item": {
                "name": "string",
                "price": 1,
                "is_offer": False,
                "url": "http://127.0.0.1",
            },
            "importance": 5
        })
    print(r.json())
    print(r.headers)
    print(r.status_code)  # 200


def test_put_items():
    r = requests.put(
        url='http://127.0.0.1:8000/items/12',
        json={
            'name': 'avatar',
            'url': 'https://errors.pydantic.dev',
            'price': 1,
        })
    print(r.json())
    print(r.headers)
    print(r.status_code)  # 201


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
    test_get_items()
