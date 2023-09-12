package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"time"
)

var client = http.Client{Timeout: time.Second * 5} // 设置超时时间

func Get() {
	req, _ := http.NewRequest("GET", "http://httpbin.org/get?a=1&b=2", nil)
	req.Header.Set("name", "atlas") // 设置请求头
	req.Header.Set("User-Agent", "python")
	req.Host = "baidu.com" // 请求头的host只能通过这种方式更改
	resp, _ := client.Do(req)
	//resp,_ := client.Get("http://httpbin.org/get?a=1&b=2")  // 如果不需要设置请求头可以直接这么用,内部做了对NewRequest的封装
	defer resp.Body.Close()
	body, _ := ioutil.ReadAll(resp.Body)
	fmt.Printf(string(body))
}

// 发送json数据的post请求
func Post() {
	data := map[string]interface{}{
		"name": "sakura",
		"age":  23,
	}
	bytesData, _ := json.Marshal(data)
	req, _ := http.NewRequest("POST", "http://httpbin.org/post", bytes.NewReader(bytesData))
	req.Header.Set("content-type", "application/json")
	resp, _ := client.Do(req)
	//resp, _ := client.Post("http://httpbin.org/post","application/json",bytes.NewReader(bytesData))
	defer resp.Body.Close()
	body, _ := ioutil.ReadAll(resp.Body)
	fmt.Printf(string(body))
}

func main() {
	Get()
	Post()
}
