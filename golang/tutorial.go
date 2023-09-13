package main

import (
	"fmt"
	"strings"
	"unicode/utf8"
)

/*
go get -v -u github.com/gin-gonic/gin   # v显示日志,u代表发现已安装包会强制更新,会在go.mod文件新增 require github.com/gin-gonic/gin
go mod init name 创建一个项目后执行,在项目里面生成一个go.mod的文件
go mod tidy 清理不用的包,下载需要的包（直接go run也会自动下载依赖的包）
go env -w GOPRIVATE="*.cmcm.com"
go env 查看变量配置
go build hello.go 把go的源文件编译并且和它所依赖的包打包成可执行文件
go run -race hello.go 执行go代码(不打包),race会对代码做竞争检测

Go语言没有类和继承的概念,它通过接口(interface)来实现多态
主协程退出,其他子协程也要跟着退出,Goroutine没有ID号
可变参数可以用结构体指针,这样如果使用者不想传,可以直接用空指针
*/

func testString() {
	str := "AB中C"                  // 字符串底层是一个 byte 数组,因此 string 也可以进行切片处理,字符串是不可变对象,无法被修改
	for index, char := range str { // 通过观察index可以发现"中"占了3字节
		fmt.Printf("%c starts at byte %d\n", char, index)
		//A starts at byte 0
		//B starts at byte 1
		//中 starts at byte 2
		//C starts at byte 5
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

func main() {
	testString()
}
