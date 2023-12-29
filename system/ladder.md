### Step 1(Shadowsocks)
```shell
pip install git+https://github.com/shadowsocks/shadowsocks.git@master
vim /etc/shadowsocks.json
{
    "server":"47.75.73.29",
    "server_port":8080,
    "local_address": "127.0.0.1",
    "local_port":1080,
    "password":"******",
    "timeout":60,
    "method":"rc4-md5",
    "fast_open": false
} 
sslocal -c /etc/shadowsocks.json -d start  # -d代表后台运行python,使用的是socks5代理,跟tor类似,程序要想使用也需要privoxy转发
```

### Step 2
```shell
apt install privoxy  # 有些应用只能使用https代理,访问被墙的网站等都得使用privoxy来做一次转换
vim /etc/privoxy/config
listen-address  0.0.0.0:8118  # 同一局域网下的其他设备都能访问privoxy代理,127.0.0.1意思是只有本地应用才能使用该代理
forward-socks5t   /   127.0.0.1:9050 .    # 将tor的socks代理转换成https代理
/etc/init.d/privoxy restart    # systemctl status privoxy

既然现在我们有了一个运行在8118端口的https扶墙代理,那么现在我们想让终端扶墙怎么办
将下面的代码添加到~/.bashrc即可
export http_proxy=http://192.168.1.1:8118
export https_proxy=http://192.168.1.1:8118
```

### 测试
```python
import requests
from stem import Signal
from stem.control import Controller

r = requests.get('https://check.torproject.org/?lang=zh_CN',
                 proxies={'https': 'https://127.0.0.1:8118'})  # 访问被墙的网址，请求的这一层只能走https代理
print(r.text)
r = requests.get('https://httpbin.org/ip', proxies={'https': 'socks5://127.0.0.1:9050'})  # tor
print(r.json()['origin'])
r = requests.get('https://httpbin.org/ip', proxies={'https': 'socks5://127.0.0.1:1080'})  # shadowsocks
print(r.json()['origin'])
r = requests.get('https://httpbin.org/ip')  # local
print(r.json()['origin'])

with Controller.from_port(port=9051) as controller:  
    # tells us how many bytes Tor has sent and received since it started
    controller.authenticate()  # provide the password here if you set one
    controller.signal(Signal.NEWNYM)
    controller.signal(Signal.HUP)
    read = controller.get_info("traffic/read")
    written = controller.get_info("traffic/written")
    print(f"Tor relay has read {read} bytes and written {written}.")
# 在可以使用SOCKS5代理的情况下尽量使用SOCKS5模式,HTTP(S)代理模式本质上是二重代理(把HTTP请求通过上级SOCKS5代理转发),对性能有一定的影响
```

```
onion
https://3g2upl4pq6kufc4m.onion/
http://torlinkbgs6aabns.onion/
http://zqktlwi4fecvo6ri.onion/wiki/index.php/Main_Page
http://thehiddenwiki.org/
https://check.torproject.org/?lang=en_US
https://torcheck.xenobite.eu/

内网地址
A类: 10.0.0.0~10.255.255.255
B类: 172.16.0.0~172.31.255.255
C类: 192.168.0.0~192.168.255.255
```

