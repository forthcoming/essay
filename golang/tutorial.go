package main

import (
	"fmt"
	"strings"
	"unicode/utf8"
	//lib "aaa"  导入包并起别名
	//_ "aaa"  匿名导入包,无法使用包里的内容,但能执行包里的init函数
)

/*
二元运算符优先级
Precedence    Operator
    5             *  /  %  <<  >>  &  &^
    4             +  -  |  ^
    3             ==  !=  <  <=  >  >=
    2             &&
    1             ||
1<<1 + 1<<1 go返回4,python返回8

go get -v -u github.com/gin-gonic/gin   # v显示日志,u代表发现已安装包会强制更新,会在go.mod文件新增 require github.com/gin-gonic/gin
go mod init name 创建一个项目后执行,在项目里面生成一个go.mod的文件
go mod tidy 清理不用的包,下载需要的包（直接go run也会自动下载依赖的包）
go env -w GOPRIVATE="*.baidu.com"
go env 查看变量配置
go build hello.go 把go的源文件编译并且和它所依赖的包打包成可执行文件
go run -race hello.go 执行go代码(不打包),race会对代码做竞争检测

Go语言没有类和继承的概念,它通过接口(interface)来实现多态
主协程退出,其他子协程也要跟着退出,Goroutine没有ID号
可变参数可以用结构体指针,这样如果使用者不想传,可以直接用空指针
*/

const pay = "Wechat"                         // 常量在编译期间确定, 无法被修改
var OpenError = fmt.Errorf("could not open") // 自定义错误

func init() {
	// 没有参数和返回值,不能在代码中主动调用他
	// 包里面所有的init函数(应为一个包可能含多个文件,每个文件一个init函数)在包被导入或者调用时被执行
	// 如果main包导入了slave包,则会先执行slave包的init函数,再执行main包的init函数
	// 执行时机 全局申明 -> init() -> main()
	fmt.Println(pay)
}

func testString() {
	str := "AB中C"                  // 字符串底层是一个 byte 数组,因此 string 也可以进行切片处理,字符串是不可变对象,无法被修改
	for index, char := range str { // 观察index发现"中"占了3字节,字符默认是int32类型
		fmt.Printf("%c=%v starts at byte %d\n", char, char, index)
		//A=65 starts at byte 0
		//B=66 starts at byte 1
		//中=20013 starts at byte 2
		//C=67 starts at byte 5
	}
	for i := 0; i < len(str); i++ { // 返回字符串中字节的数量
		fmt.Printf("%d\t", str[i]) // 65      66      228     184     173     67
	}
	fmt.Println("\n", utf8.RuneCountInString(str)) // 4

	// 如果想修改字符串,必须先转换为[]byte或者[]rune再修改
	str1 := "welcome"
	str1Byte := []byte(str1) // 按字节处理,也可以按字符处理
	str1Byte[0] = 'W'
	str1 = string(str1Byte)
	str2 := "李佳芮"
	str2Rune := []rune(str2) // 按字符处理,应为一个中文占多个字节
	str2Rune[2] = '瑞'
	str2 = string(str2Rune)
	fmt.Println(str1, str2) // Welcome 李佳瑞

	strings.Contains("seafood", "foo")                // true
	strings.Join([]string{"foo", "bar", "baz"}, ", ") // foo, bar, baz
	strings.Index("chicken", "ken")                   // 4, substr不存在返回-1
	strings.Split("a,b,c", ",")                       // [a b c]
	strings.Replace("oink oink oink", "o", "l", 2)    // link link oink, n表示替换的次数,小于0表示全部替换
}

func testDefinition() {
	var a int // int类型默认初始值为0, var可以初始化全局变量
	fmt.Println("a=", a)

	b := "hello"        // 自动类型推导为string, :=操作符要求至少有一个变量尚未声明,不能初始化全局变量
	b, c := "world", 50 // b已经声明,但c尚未声明
	b, c = "oracle", 90 // 给已经声明的变量b和c赋新值
	fmt.Println("changed b is", b, "c is", c)
}

func testFunction(a float64, b bool) ([]int, bool) { // 单个返回值不用()
	// func name() (a, b int, c bool) { return }  返回值可以带上变量名,函数结束直接return即可,相同类型返回值可以合并声明
	return []int{int(a)}, !b
}

func main() {
	//testString()
	//testDefinition()
	fmt.Println(testFunction(1.2, false))
}
