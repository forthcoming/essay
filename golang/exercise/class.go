package main

import (
	"fmt"
	"strconv"
)

// 结构体是值类型; 如果结构体包含不可比较的字段,则结构体也不可比较; 如果它的每一个字段都可比较,则该结构体也可比较(==和!=)
// 如果函数返回值定义了结构体指针变量, 则该变量是空指针类型
type Book struct { // 结构体成员顺序也有重要意义,如果交换title和author顺序,那样的话就是定义了不同的结构体类型
	title  string
	author string
	bookId int
	next   *Book // 一个命名为S的结构体类型将不能再包含S类型的成员,但是S类型的结构体可以包含*S指针类型的成员
}

func main() {
	/****************************** 基本使用 ******************************/
	book1 := Book{"C++", "sakura", 1, nil} // 结构体初始化的时候要么全用key-value形式,要么全用value形式,后者只能按成员声明顺序一一赋值
	book2 := Book{title: "Go", bookId: 2}  // 忽略的字段用默认值
	book3 := new(Book)                     // 等价于 book3 := &Book{}
	var book4 Book                         // 等价于 book4 := Book{}

	var book5 *Book // 此时book5还是nil的空指针,未分配实际内存
	// book5.bookId = 5     // 错误写法, 当结构体指针为nil时只能被赋一个拥有实际存储地址的结构体指针后, 才能访问自己的成员变量
	book5 = book3
	book5.title = "Python" // 结构体指针访问成员方式跟结构体变量一样
	fmt.Println(book1, book2, book3, book4)

	employee := struct {
		firstName, lastName string
		age                 int
	}{
		firstName: "Lucas",
		lastName:  "Nikola",
		age:       31,
	}
	fmt.Println("匿名结构体", employee)
	/****************************** 基本使用 ******************************/

	/****************************** 遍历 ******************************/
	book6 := []Book{
		{"C++", "sakura", 12, nil},
		{"Go", "neo", 22, nil},
	}
	var book6ptr []*Book
	for _, book := range book6 {
		book.bookId /= 2                   // 此处book是值拷贝,不会影响到book6
		book6ptr = append(book6ptr, &book) // 错误写法,应为遍历过程中book的地址始终不变,只有值在变
	}
	fmt.Println(book6, book6ptr)

	book7 := book6
	for idx := range book7 {
		book7[idx].bookId /= 2 // 由于book6是切片,因此改变book7会影响到book6
	}
	fmt.Println(book6)

	book8 := []*Book{
		{"C++", "sakura", 12, nil},
		{"Go", "neo", 22, nil},
	}
	var book8ptr []*Book
	for _, book := range book8 {
		book.bookId /= 2                  // 此处book是指针的值拷贝,会影响到book8
		book8ptr = append(book8ptr, book) // 正确写法
	}
	fmt.Println(book8, book8ptr)
	/****************************** 遍历 ******************************/

	/****************************** 多态+继承+覆盖 ******************************/
	// mate30无法直接调用Huawei结构体的成员变量,如mate30.name
	// Huawei必须实现Phone接口的所有方法
	var mate30 Phone = &Huawei{name: "Mate 30", price: 3999}
	mate30.call()
	mate30.seenMessage()

	pro := HuaweiPro{Huawei: Huawei{name: "huawei pro", price: 6999}, camera: "camera"} // 匿名成员的key就是其类型本身
	var proPtr Phone = &pro                                                             // HuaweiPro包含了匿名字段类型Huawei,所以继承了匿名字段的函数和变量,所以也是实现了Phone接口
	proPtr.call()
	proPtr.seenMessage()
	pro.echo()
	fmt.Println(pro, pro.Huawei.name, pro.name, pro.price, pro.camera)
	/****************************** 多态+继承+覆盖 ******************************/

}

/****************************** 接口定义 ******************************/
type Phone interface { // 如果一个类型实现了一个接口中所有方法,我们说类型实现了该接口,go没有显式的关键字用来实现接口
	call()
	seenMessage()
}

// 接口嵌套
type MobilePhone interface {
	Phone
}

/****************************** 接口定义 ******************************/

/****************************** 接口实现 ******************************/
type Huawei struct {
	name   string
	price  float64
	GetUID func(token string) (int64, error)
}

func (h *Huawei) call() { // 这里Huawei是指针,无论传入的h是指针还是值类型,都会更改h本身; 可以给内置类型如int增加方法,前提是用type给int定义命名类型
	h.name = "banana"
	fmt.Printf("%s 有打电话功能.....\n", h.name)
}
func (h *Huawei) seenMessage() {
	fmt.Printf("%s 有发短信功能.....\n", h.name)
}
func (h Huawei) String() string { // 自定义格式化输出
	return "❰ " + strconv.FormatInt(int64(h.price), 10) + " ❱"
}
func (h Huawei) echo() {
	fmt.Println("in huawei")
}

type HuaweiPro struct {
	Huawei // 继承了Huawei的成员变量及接口方法
	camera string
}

func (h HuaweiPro) echo() { // 只需要名字相同,即可重写匿名字段的方法
	fmt.Println("in huawei pro")
}

/****************************** 接口实现 ******************************/
