### Step 0(Lantern)
```shell
wget https://github.com/getlantern/lantern-binaries/raw/main/lantern-installer-preview-64-bit.deb
dpkg -i lantern

git clone https://github.com/getlantern/lantern.git
cd lantern
make lantern
./lantern

Manage system proxy    
Proxy all traffic   # 所有请求都走代理(默认只有部分请求走代理)
HTTP(S) proxy: 127.0.0.1:42787
SOCKS proxy: 127.0.0.1:33947
```

### Step 0(Shadowsocks)
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

### Step 1
```shell
curl https://www.torproject.org/dist/torbrowser/13.0.8/tor-browser-linux-x86_64-13.0.8.tar.xz -o tor.tar.xz
tar xzf tor.tar.gz
cd tor
./configure && make  # Now you can run tor as src/or/tor, or you can run make install to install it into /usr/local/ and then you can start it just by running tor.
make install

vim /usr/local/etc/tor/torrc
HTTPSProxy 127.0.0.1:42787 # 前置代理端口(lantern)
#Socks5Proxy 127.0.0.1:1080     # 前置代理端口(Shadowsocks),也可以选择宿主机下的Shadowsocks作为前端代理,一定要记得勾选Shadowsocks的"允许来自局域网的连接"选项
MaxCircuitDirtiness 10  # default 10 minutes as long as the circuit is working fine.tor自身限制最少10s換一次identity
ControlPort 9051  # 控制程序(如stem)访问的端口
SocksPort 127.0.0.1:9050  # default 9050,外部程序访问Tor的端口,This directive can be specified multiple times to bind to multiple addresses/ports.
SocksPort 192.168.2.107:9050
ClientOnly 1   # If set to 1, Tor will not run as a relay or serve directory requests

tor
pkill -sighup tor
[notice] Read configuration file "/usr/local/etc/tor/torrc".
[notice] Opening Socks listener on 127.0.0.1:9050
[notice] You configured a non-loopback address '192.168.2.107:9050' for SocksPort. This allows everybody on your local network to use your machine as a proxy. Make sure this is what you wanted.
[notice] Opening Control listener on 127.0.0.1:9051
[notice] Parsing GEOIP IPv4 file /usr/local/share/tor/geoip.
[notice] Parsing GEOIP IPv6 file /usr/local/share/tor/geoip6.
[warn] You are running Tor as root. You don't need to, and you probably shouldn't.
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

