package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

/*
f2返回结构体比f1返回指针更快
f2结构体在栈空间分配,f1结构体在堆内存分配
经测试1M以内返回结构体速度更快
堆上分配内存比栈慢原因:
堆上分配内存的函数runtime.newobject本身逻辑复杂
堆上分配内存后期需要gc对其内存回收
逃逸分析(escape analysis): 当发现变量的作用域没有跑出函数范围，就可以在栈上，反之则必须分配在堆
func main() {
	mainVal := func() *int {
		fooVal := 11  // moved to heap: fooVal
		return &fooVal
	}()
	println(*mainVal)
}
https://golang.org/ref/mod

go tool pprof
https://www.cnblogs.com/chnmig/p/16744250.html
https://www.kandaoni.com/news/21726.html
https://xie.infoq.cn/article/56c801b339241fd80c3b8f616
https://blog.xizhibei.me/2021/06/27/golang-heap-profiling/
顺便看看go tool trace
*/

var client = http.Client{Timeout: time.Second * 5} // 设置超时时间

func Get() {
	req, _ := http.NewRequest("GET", "http://httpbin.org/get?a=1&b=2", nil)
	req.Header.Set("name", "atlas") // 设置请求头
	req.Header.Set("User-Agent", "python")
	req.Host = "baidu.com" // 请求头的host只能通过这种方式更改
	resp, _ := client.Do(req)
	//resp,_ := client.Get("http://httpbin.org/get?a=1&b=2")  // 如果不需要设置请求头可以直接这么用,内部做了对NewRequest的封装
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	fmt.Printf(string(body))
}

// Post 发送json数据的post请求
func Post() {
	data := map[string]any{
		"name": "sakura",
		"age":  23,
	}
	bytesData, _ := json.Marshal(data)
	req, _ := http.NewRequest("POST", "http://httpbin.org/post", bytes.NewReader(bytesData))
	req.Header.Set("content-type", "application/json")
	resp, _ := client.Do(req)
	//resp, _ := client.Post("http://httpbin.org/post","application/json",bytes.NewReader(bytesData))
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	fmt.Printf(string(body))
}

var begin = time.Now()

func log(text string) {
	fmt.Println(time.Since(begin), "\t", text)
}

func mark(task string) func() {
	log(" ==> " + task + "...")
	return func() {
		log("<==  " + task + "...")
	}
}

// Tasks

func task1(ctx context.Context) {
	defer mark("task_1")()
	task2(ctx)
}

func task2(ctx context.Context) {
	defer mark("task_2")()
	//	Create a cancelable context
	ctx2, cancel := context.WithCancel(ctx)
	defer cancel()

	//	Call following tasks
	task3(ctx2)
}

func task3(ctx context.Context) {
	defer mark("task_3")()
	//	Create a context with 5 seconds timeout
	ctx3, cancel := context.WithTimeout(ctx, time.Second*5)
	defer cancel()

	//	Call following tasks
	go task4(ctx3)
	go task5(ctx3)

	//	wait until be canceled
	select {
	case <-ctx3.Done():
		log("task3: <- context.Done()")
	}
}

func task4(ctx context.Context) {
	defer mark("task_4")()
	//	Create a context with 3 seconds timeout
	ctx4, cancel := context.WithTimeout(ctx, time.Second*3)
	defer cancel()

	//	wait until be canceled
	select {
	case <-ctx4.Done():
		log("task4: <- context.Done()")
	}
}

func task5(ctx context.Context) {
	defer mark("task_5")()
	//	Create context with 5 seconds timeout
	ctx5, cancel := context.WithTimeout(ctx, time.Second*6)
	defer cancel()

	//	Call following tasks
	go task6(ctx5)

	//	wait until be canceled
	select {
	case <-ctx5.Done():
		log("task5: <- context.Done()")
	}
}

func task6(ctx context.Context) {
	defer mark("task_6")()
	//	Create a context with a value in it
	ctx6 := context.WithValue(ctx, "userID", 12)

	//	wait until be canceled
	select {
	case <-ctx6.Done():
		log("task6: <- context.Done()")
	}
}

func main() {
	Get()

	task1(context.Background())
	/*
	       task1
	         | 顺序
	       task2
	         | 顺序
	       task3
	   协程 /   \ 协程
	    task4 task5
	            | 协程
	          task6
	*/
}
