package main

import (
	"fmt"
	"math/rand"
	"os"
	"strconv"
	"strings"
	"time"
	"unicode/utf8"
)

const PAY = "Wechat"                         // 常量的值在编译的时候确定, 无法被修改赋值
var character = '你'                          // 申明全局变量时无法使用:=这种方式, 字符在go里面默认是int32类型
var OpenError = fmt.Errorf("could not open") // 自定义错误

/*
go mod init name 创建一个项目后执行,在项目里面生成一个go.mod的文件
go get -v -u github.com/gin-gonic/gin   # v显示操作流程的日志及信息,u代表发现已安装包会强制更新.会在go.mod文件新增 require github.com/gin-gonic/gin
go mod tidy 清理不用的包,下载需要的包（直接go run也会自动下载依赖的包）
go env -w GOPRIVATE="*.cmcm.com"
go env 查看变量配置
go build hello.go 把go的源文件编译并且和它所依赖的包打包成可执行文件
go run -race hello.go 执行go代码(不打包),race会对代码做竞争检测

Go语言没有类和继承的概念，它通过接口（interface）来实现多态
主协程退出了，其他子协程也要跟着退出,Goroutine没有ID号
可变参数可以用结构体指针，这样如果使用者不想传，可以直接用空指针

When declaring an empty slice, prefer
var t []string
over
t := []string{}
The former declares a nil slice value, while the latter is non-nil but zero-length. They are functionally equivalent—their len and cap are both zero—but the nil slice is the preferred style.
Note that there are limited circumstances where a non-nil but zero-length slice is preferred, such as when encoding JSON objects (a nil slice encodes to null, while []string{} encodes to the JSON array []).
When designing interfaces, avoid making a distinction between a nil slice and a non-nil, zero-length slice, as this can lead to subtle programming errors.
*/

func init() {
	// 包里面所有的init函数(应为一个包可能含多个文件,每个文件一个init函数)在包被导入或者调用时被执行
	// 没有参数和返回值,不能在代码中主动调用他
	// 如果main包导入了slave包,则会先执行slave包的init函数,再执行main包的init函数
	// 执行时机 全局申明 -> init() -> main()
	rand.Seed(time.Now().UnixNano()) // 随机种子
	fmt.Printf("character is %v \n", character)
}

func mistake() {
	value := 2

	defer func(value int) { // Use this deferred function to handle errors.
		err := recover() // 只有在相同的 Go 协程中调用 recover 才管用,recover 不能恢复一个不同协程的 panic
		if err != nil {
			fmt.Printf("1. value: %d error: %v\n", value, err) // 输出2, 并非在调用延迟函数的时候才确定实参,而是当执行 defer 语句的时候就会对延迟函数的实参进行求值
		}
	}(value)

	defer func(value int) { // 当一个函数内多次调用defer时,按后进先出顺序执行
		fmt.Printf("2. value: %d\n", value)
	}(value)

	value = 22
	panic("make mistakes")
	fmt.Println("不会再被执行") // 不会再被执行
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

func isEmptyArray() {
	x := []int{}
	y := make([]int, 0)
	var z []int
	fmt.Println(len(x), len(y), len(z), x == nil, y == nil, z == nil) // 0 0 0 false false true
	// 取元素之前一定要先判断是否为空,判断数组是否为空一律用len方式,防止出错
}

func main() {
	shadowedTest()

	isEmptyArray()

	mistake()

	testValue1 := 1
	fmt.Println(Count(testValue1, 2, 3), testValue1) // testValue1的值不会被Count改变
	testValue2 := []int{2, 3, 4}
	fmt.Println(Count(testValue2...), testValue2) // ...类似于python的解引用,可以不给Count传参,testValue2的值会被Count改变

	str := "ABC中国"                 // 字符串底层是一个 byte 数组,因此 string 也可以进行切片处理,字符串是不可变对象,无法被修改
	for index, char := range str { // 通过观察index可以发现"中"占了3字节
		fmt.Printf("%c starts at byte %d\n", char, index)
	}
	fmt.Println()
	for i := 0; i < len(str); i++ { // 返回字符串中字节的数量
		fmt.Printf("%d\t", str[i]) // 65      66      67      228     184     173     229     155     189
	}
	fmt.Println("\n", utf8.RuneCountInString(str)) // 5

	// 如果想修改字符串,必须先转换为[]byte或者[]rune再修改
	str1 := "welcome"
	str1Byte := []byte(str1) // 按字节处理,也可以按字符处理
	str1Byte[0] = 'W'
	str1 = string(str1Byte)
	str2 := "李佳芮"
	str2Rune := []rune(str2) // 按字符处理,应为一个中文占多个字节
	str2Rune[2] = '瑞'
	str2 = string(str2Rune)
	fmt.Println(str1, str2)

	// 简短声明的语法要求 := 操作符的左边至少有一个变量是尚未声明的
	a, b := 20, 30 // 声明变量a和b
	fmt.Println("a is", a, "b is", b)
	b, c := 40, 50 // b已经声明，但c尚未声明
	fmt.Println("b is", b, "c is", c)
	b, c = 80, 90 // 给已经声明的变量b和c赋新值
	fmt.Println("changed b is", b, "c is", c)

	userFile := "note.txt"
	fOut, _ := os.OpenFile(userFile, os.O_RDWR|os.O_CREATE, 0666)
	defer fOut.Close()
	for i := 0; i < 5; i++ {
		_, _ = fOut.WriteString("write string!\n")
		_, _ = fOut.Write([]byte("write byte!\n"))
	}

	fmt.Println(strings.Contains("seafood", "foo"))
	s := []string{"foo", "bar", "baz"}
	fmt.Println(strings.Join(s, ", "))
	fmt.Println(strings.Index("chicken", "ken")) // 4
	fmt.Println(strings.Index("chicken", "dmr")) // -1

	// n表示替换的次数, 小于0表示全部替换
	fmt.Println(strings.Replace("oink oink oink", "k", "ky", 2))      // oinky oinky oink
	fmt.Println(strings.Replace("oink oink oink", "oink", "moo", -1)) // moo moo moo
	fmt.Printf("%v\n", strings.Split("a,b,c", ","))                   // [a b c]
	fmt.Println(strconv.FormatBool(false), strconv.FormatInt(1234, 10))
	myBool, _ := strconv.ParseBool("false")
	myFloat, _ := strconv.ParseInt("111", 2, 64) // 7
	fmt.Println(myBool, myFloat)
	/*
		%b : 二进制
		%c : 字符
		%d : 整数
		%f : 浮点数
		%t : bool类型
		%s : 字符串
		%T : 变量类型
		%v : 默认格式输出(通用输出格式)
	*/
	formatString := fmt.Sprintf("%04d", rand.Intn(5)) // 04意思是长度为4,不足的前面用0补齐;返回[0,5)范围内伪随机整数,使用前一定要重置随机种子(py会自动执行这一步)
	fmt.Println(formatString)

	myMap := map[int]string{22: "sun", 33: "avatar"} // Map无序,是引用操作
	//var myMap map[int]string
	myMap[11] = "\"oracle\"" // 转义字符
	value, isOK := myMap[11]
	delete(myMap, 22)               // 删除不存在的key不会报错
	fmt.Println(myMap, value, isOK) // 访问不存在的key不会报错,会返回默认值,isOk是False

	var inter interface{} = 12                                           // 所有类型都实现了空接口,所以可以接受所有类型变量,println就是这么实现
	result, ok := inter.(int)                                            // 类型断言,判断正确了,result即为断言的值,前提是被断言的变量是接口类型
	fmt.Printf("result: %d, ok: %t, valueType: %T\n", result, ok, inter) // reflect.TypeOf(args)
	switch v := inter.(type) {                                           // 只能在switch语法中使用
	case nil:
		fmt.Printf("%s is nil\n", v)
	case string:
		fmt.Printf("%s is string\n", v)
	case int:
		fmt.Printf("%d is int\n", v)
	}

	queryTime := time.Date(2021, time.Month(4), 1, 0, 0, 0, 0, time.Local)
	queryTime = queryTime.AddDate(0, -1, 0)
	before := queryTime.Add(-2 * time.Second)                                                   // Add是给现有时间加减分钟或者小时,Sub是前一个时间减后一个时间的时差
	o := before.Sub(queryTime)                                                                  // before - queryTime, 返回time.Duration类型
	fmt.Println(o > 0, queryTime.Unix())                                                        // false, Unix返回秒级整形时间戳
	fmt.Println(queryTime.UnixNano(), queryTime.UnixNano()/1e9)                                 // UnixNano返回纳秒级整形时间戳,1秒等于10^9纳秒
	fmt.Println(time.Now().Format("2006-01-02 15:04:05"))                                       // 记忆诀窍: 2006年12345,也可以2006-01-02 03:04:05但有区别
	fmt.Println(time.ParseInLocation("2006-01-02 15:04:05", "2021-01-21 14:30:00", time.Local)) // 字符串转时间
	fmt.Println(time.Now().Format("04:05"))
	fmt.Println(time.Unix(queryTime.Unix(), 0)) // 将时间戳转换为时间
	//Nanosecond  Duration = 1                  // 纳秒
	//Microsecond          = 1000 * Nanosecond  // 微秒
	//Millisecond          = 1000 * Microsecond // 毫秒
	//Second               = 1000 * Millisecond

	local := 15
	switch local {
	case 1, 2:
		fmt.Println("1111")
	case 15:
		fmt.Println("3333")
		fmt.Println("三三三")
		// 不需要加break
		fallthrough // 强制执行后一个case语句块
	case 20:
		fmt.Println("4444")
	default:
		fmt.Println("default")
	}
}
