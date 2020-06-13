'''
When you make a request, Requests makes educated guesses about the encoding of the response based on the HTTP headers.
The text encoding guessed by Requests is used when you access r.text. 
You can find out what encoding Requests is using, and change it, using the r.encoding property:
>>> r.encoding
'utf-8'
>>> r.encoding = 'ISO-8859-1'
If you change the encoding, Requests will use the new value of r.encoding whenever you call r.text.
You might want to do this in any situation where you can apply special logic to work out what the encoding of the content will be.
For example, HTTP and XML have the ability to specify their encoding in their body. In situations like this, you should use r.content to find the encoding, and then set r.encoding.
This will let you use r.text with the correct encoding.
Requests will also use custom encodings in the event that you need them.
If you have created your own encoding and registered it with the codecs module, you can simply use the codec name as the value of r.encoding and Requests will handle the decoding for you.
'''

###############################################################################################
# 请求参数
import requests
url='http://httpbin.org/get'
#Custom headers are given less precedence than more specific sources of information
headers = {
  'user-agent': 'my custom user agent',
  'cookie': 'name=caonima',
}
#优先级低于headers中的Cookie字段
cookies = {
  'name':'fucker',
}
proxies = {
  "http":"http://HNF03B86XW5CH2BP:59C97910FF30A87F@proxy.abuyun.com:9010",
  "https":"https://HNF03B86XW5CH2BP:59C97910FF30A87F@proxy.abuyun.com:9010",
  "https":"socks5://127.0.0.1:9050",   # pip install requests[socks],socks速度比https要快
}
#If you specify a single value for the timeout like timeout=5 ,The timeout value will be applied to both the connect and the read timeouts.
#Specify a tuple if you would like to set the values separately like timeout=(3.05, 27)
#If the remote server is very slow, you can tell Requests to wait forever for a response like timeout=None
#allow_redirects参数为False则表示不会主动重定向
r=requests.get(url,headers=headers,cookies=cookies,proxies=proxies,timeout=10,allow_redirects=False)
print(r.text)

###############################################################################################
# 当data类型是json时,一般还需要在头信息中说明Content-Type=application/json; charset=UTF-8
# post提交头信息才会包含Content-Length和Content-Type字段,因此不应该出现在get的头信息中
# POST请求
import requests
import json
#data will automatically be form-encoded when the request is made
data= {"user":"xlzd", "pass": "mypassword"}
requests.post("http://xlzd.me/login",data=data) 
#This is particularly useful when the form has multiple elements that use the same key
data=(('key1', 'value1'), ('key1', 'value2'))
requests.post("http://httpbin.org/post", data=data) 
#There are times that you may want to send data that is not form-encoded.
#If you pass in a string instead of a dict, that data will be posted directly
data={'some': 'data'}
requests.post("https://api.github.com/some/endpoint",data=json.dumps(data)) 

###############################################################################################
# response对象
import requests
r = requests.get('http://xlzd.me')
print(r.status_code)
#list contains the Response objects that were created in order to complete the request.
#The list is sorted from the oldest to the most recent response.
#We can use the history property of the Response object to track redirection.
print(r.history)
print(r.request)
print(r.encoding)
print(r.headers)  # server's response headers
print(r.cookies)
print(r.text)     #str
print(r.content)  #bytes
print(r.json())

###############################################################################################
# URL参数解析
# 在GET请求的时候,经常会有很多查询参数接在URL后面,形如http://xlzd.me/query?name=xlzd&lang=python
# 在拼接URL的时候常常容易出现拼接错误的情况,对此你可以使用如下代码让这个过程变得简洁明了
import requests
from urllib.parse import urlencode,quote,unquote
'''
urlencode:对字典编码
quote:对字符串编码
unquote:对字符串解码
有些网站如1688是对gbk进行编码,所以正确编码姿势是quote('男鞋',encoding='gbk')
'''
params={"name":"Mr.王", "color": "red & black"}
r = requests.get("https://xlzd.me/query", params=params)   # 注意get也有data和json参数,跟post类似,post也可以有params
print(r.url) #https://xlzd.me/query?name=Mr.%E7%8E%8B&color=red+%26+black
r=requests.get(f"http://xlzd.me/query?name={quote(params['name'])}&color={quote(params['color'])}")
print(r.url) #https://xlzd.me/query?name=Mr.%E7%8E%8B&color=red%20%26%20black
r = requests.get(f"http://xlzd.me/query?{urlencode(params)}")
print(r.url) #https://xlzd.me/query?name=Mr.%E7%8E%8B&color=red+%26+black
r = requests.get(f"http://xlzd.me/query?name={params['name']}&color={params['color']}") #Error
print(r.url) #https://xlzd.me/query?name=Mr.%E7%8E%8B&color=red%20&%20black
print(unquote(urlencode(params))) #name=Mr.王&color=red+&+black

###############################################################################################
# Session
# 如果你向同一主机发送多个请求,底层的TCP连接将会被重用,nginx通过keepalive_timeout参数设置,从而带来显著的性能提升
import requests
data={
  'Username':'avatar',
  'Password':'caonima123',
  'verify':'',
  'Action':'indexLogin',
}
head = {
  'User-Agent': 'agent-user',
}
s=requests.Session()
print(s.headers) #客户端请求的默认参数 {'User-Agent': 'python-requests/2.9.1','Accept': '*/*'}
print(s.cookies) #服务器返回来的cookies信息 <RequestsCookieJar[]>

r=s.post('https://www.ttz.com/Member/login',data=data,headers=head) #head只在本次请求有效,会覆盖已有字段,但本次请求头包含了r的head和s的head
print(s.headers) #{'User-Agent': 'python-requests/2.9.1', 'Accept': '*/*'}
print(s.cookies) #<RequestsCookieJar[Cookie(name='UserId',value='81577753'),Cookie(name='UserIdKey',value='f35'),Cookie(name='PHPSESSID',value='tqk')]>
#服务器返回来的cookies信
print(r.cookies) #<RequestsCookieJar[Cookie(name='UserId',value='81577753'),Cookie(name='UserIdKey',value='f35'),Cookie(name='PHPSESSID',value='tqk')]>
#客户端头信息
print(r.request.headers) #{'User-Agent': 'agent-user','Accept': '*/*'}
#服务端头信息,不含cookie,user-agent信息
print(r.headers) #{'Expires': 'Thu, 19 Nov 1981 08:52:00 GMT', 'Server': 'nginx','Set-Cookie': 'PHPSESSID=tqk;UserId=81577753;UserIdKey=f35'}

r=s.get('https://www.ttz.com/')
print(s.headers) #{'User-Agent': 'python-requests/2.9.1','Accept': '*/*'}
print(s.cookies) #<RequestsCookieJar[Cookie(name='UserId',value='81577753'),Cookie(name='UserIdKey',value='f35'),Cookie(name='PHPSESSID',value='tqk')]>
#自动带上了s的cookies信息和s的头信息
print(r.request.headers) #{'User-Agent': 'python-requests/2.9.1', 'Cookie': 'PHPSESSID=tqk; UserId=81577753; UserIdKey=f35','Accept': '*/*'}
print(r.headers) #{'Server': 'nginx','Content-Encoding': 'gzip'}
print(r.cookies) #<RequestsCookieJar[]>

# Any dictionaries that you pass to a request method will be merged with the session-level values that are set.
# The method-level parameters override session parameters.
# however, that method-level parameters will not be persisted across requests, even if using a session.
# This example will only send the cookies with the first request, but not the second:
s = requests.Session()
r = s.get('http://httpbin.org/cookies', cookies={'from-my': 'browser'})
print(r.text)    # '{"cookies": {"from-my": "browser"}}'
r = s.get('http://httpbin.org/cookies')
print(r.text)    # '{"cookies": {}}'
