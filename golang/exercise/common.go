package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strconv"
	"time"
)

/*
go tool compile -l -m hello.go  # -m让编译器告诉我们变量到底是在堆还是栈分配
go tool objdump hello.o

f2返回结构体比f1返回指针更快
f2结构体在栈空间分配,f1结构体在堆内存分配
经测试1M以内返回结构体速度更快
堆上分配内存比栈慢原因:
堆上分配内存的函数runtime.newobject本身逻辑复杂
堆上分配内存后期需要gc对其内存回收

逃逸分析:
假设有变量v及指向v的指针p,如果p的生命周期大于v,则v需要在堆上分配内存
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

func Count(values ...int) int { // 可变参数
	total := 0
	fmt.Printf("values's type is %T, cap: %d, len: %d\n", values, cap(values), len(values)) // []int
	for _, val := range values {
		total += val
	}
	values[0] = 100              // 由于是切片传参,此处会直接影响到入参值
	values = append(values, 200) // append引起values扩容,指向了新位置,所以append不会影响到入参值
	return total
}

func shadowedTest() (str string) {
	if true {
		//str = "inner"
		//return     // 正确,如果return后不接变量,则返回的始终是返回值列表中的变量

		str := "inner"
		return str // 正确, 输出 inner
	}
	return
}

func main() {
	shadowedTest()

	testValue1 := 1
	fmt.Println(Count(testValue1, 2, 3), testValue1) // testValue1的值不会被Count改变
	testValue2 := []int{2, 3, 4}
	fmt.Println(Count(testValue2...), testValue2) // ...类似于python的解引用,可以不给Count传参,testValue2的值会被Count改变

	fmt.Println(strconv.FormatBool(false), strconv.FormatInt(1234, 10))
	myBool, _ := strconv.ParseBool("false")
	myFloat, _ := strconv.ParseInt("111", 2, 64) // 7
	fmt.Println(myBool, myFloat)

	Get()
}
