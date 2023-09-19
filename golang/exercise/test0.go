package main

import (
	"fmt"
	"unsafe"
)

// 函数,结构体,切片,指针,接口,信道的零值是nil
func main() { // 程序开始执行的函数,名字main固定,注意{不能单独一行
	var a bool // 此时的默认值是false
	a = true
	b := 12
	//b = 15.565464  // 错误,应为b被当做int类型了
	c := 13.4     // := 左侧如果没有声明新的变量，就产生编译错误,:=是一个声明并赋值的操作
	var d float64 // 声明后若不赋值，使用默认值
	d = c + 1     // 在内存中将c的值进行了拷贝，通过&取地址符可以看到他们内存地址不一样
	c, d = d, c   // 交换两个变量的值
	_ = 42        // 被用于抛弃值,是一个只写变量，你不能得到它的值
	fmt.Println("Hello" + " World!")
	fmt.Println(a, &c, &d, c, d, unsafe.Sizeof(a), b) // 如果声明了一个局部变量却没有在相同的代码块中使用它，会得到编译错误,但是全局变量是允许声明但不使用

	var ptr *float32
	if ptr == nil {
		fmt.Printf("ptr 的值为 : %x\n", ptr)
	}

	newFunction := squares()
	fmt.Println(newFunction()) // "1"
	fmt.Println(newFunction()) // "4"

	ff() // recover只是捕获本函数异常并恢复
	fmt.Println("Returned normally from ff.")

	test()

	multilineString := fmt.Sprintf(`welcome to 
%s, I'm %d years old`, "Australia", 30) // sprintf是格式化字符串给变量,printf是格式化字符串打印出来
	fmt.Println(multilineString)
}

func squares() func() int {
	var x int
	return func() int {
		x++ // 在函数中定义的内部函数可以引用该函数的变量
		return x * x
	}
}

func test() int {
	fmt.Println("before test")
	defer clean() // 执行是发生在 return之后，关键字 defer 之后是函数的调用,可以用来释放链接资源，作用就是把关键字之后的函数执行压入一个栈中延迟执行，多个 defer 的执行顺序是后进先出 ,defer表达式中可以修改函数中的命名返回值
	fmt.Println("after test")
	return 0
}
func clean() {
	fmt.Println("in clean")
}

func ff() {
	defer func() {
		r := recover()
		if r != nil {
			fmt.Println("Recovered in ff", r)
		}
	}()
	fmt.Println("Calling g.")
	g()
	fmt.Println("Returned normally from g.") // 改行不会被执行
}

func g() {
	panic("ERROR")
}
