package main

import (
	"fmt"
	"strconv"
)

// Phone 如果一个类型实现了一个接口中所有方法,我们说类型实现了该接口,go没有显式的关键字用来实现接口
type Phone interface {
	call()
	seenMessage()
}

// MobilePhone 接口嵌套
type MobilePhone interface {
	Phone
}

// Huawei 接口实现
type Huawei struct {
	name   string
	price  float64
	GetUid func(token string) (int64, error)
}

func (h *Huawei) call() { // 这里Huawei是指针,无论传入的h是指针还是值类型,都会更改h本身
	h.name = "banana"
	fmt.Printf("%s 有打电话功能.....\n", h.name)
}
func (h *Huawei) seenMessage() {
	fmt.Printf("%s 有发短信功能.....\n", h.name)
}
func (h *Huawei) String() string { // 自定义格式化输出
	return "❰ " + strconv.FormatInt(int64(h.price), 10) + " ❱"
}
func (h *Huawei) echo() {
	fmt.Println("in huawei")
}

type HuaweiPro struct {
	Huawei // 相当于继承了Huawei的成员变量及接口方法
	camera string
}

func (h *HuaweiPro) echo() { // 只需要名字相同,即可重写匿名字段的方法
	fmt.Println("in huawei pro")
}

func testInterface() {
	// 所有类型都实现了空接口,所以可以接受所有类型变量,println就是这么实现
	var inter any = 12 // type any = interface{}即any是interface{}别名
	// 类型断言,判断正确了,result即为断言的值,前提是被断言的变量是接口类型
	result, ok := inter.(int)
	fmt.Printf("result: %d, ok: %t, type: %T\n", result, ok, inter)

	switch v := inter.(type) { // 只能在switch语法中使用
	case nil:
		fmt.Printf("%s is nil\n", v)
	case string:
		fmt.Printf("%s is string\n", v)
	case int:
		fmt.Printf("%d is int\n", v)
	}
}

func main() {
	var mate30 Phone = &Huawei{name: "Mate 30", price: 3999} // 通过接口(interface)实现多态,Huawei必须实现Phone接口的所有方法
	mate30.call()                                            // mate30无法直接调用Huawei结构体的成员变量,如mate30.name
	mate30.seenMessage()

	pro := HuaweiPro{Huawei: Huawei{name: "huawei pro", price: 6999}, camera: "camera"} // 匿名成员的key就是其类型本身
	// HuaweiPro包含了匿名字段类型Huawei,所以继承了匿名字段的函数和变量,所以也是实现了Phone接口
	var proPtr Phone = &pro
	proPtr.call()
	proPtr.seenMessage()
	pro.echo()
	fmt.Println(pro, pro.Huawei.name, pro.name, pro.price, pro.camera)

	testInterface()
}
