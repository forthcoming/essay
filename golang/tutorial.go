package main

import (
	"fmt"
	"sort"
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
go env -w GOPROXY=https://goproxy.cn,direct  # 解决国内包同步问题
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

func testFunction(a *float64, b bool) ([]int, bool) { // 单个返回值不用()
	// func name() (a, b int, c bool) { return }  返回值可以带上变量名,函数结束直接return即可,相同类型返回值可以合并声明
	*a += 1
	multiPointer := &a // multiPointer类型为**float64
	**multiPointer += 1
	return []int{int(*a)}, !b
}

func testDefer() {
	value := 2

	defer func() { // 匿名函数定义
		err := recover() // 只有在相同的协程中调用recover才能处理错误
		if err != nil {
			fmt.Printf("position 1, error: %v\n", err)
		}
	}()

	defer func(value int) { // defer在函数结束时被调用(return语句之后),当一个函数内多次调用defer时,按后进先出顺序执行
		fmt.Println("position 2,", value) // 输出2, 在执行defer语句时就会对延迟函数的实参进行求值
	}(value)

	value = 10
	panic("make mistakes")
	fmt.Println("不会再被执行")
}

func testSlice() {
	/****************************** 数组 ******************************/
	// 数组是值传递
	a0 := [...]int{1, 2, 3, 4}     // [1 2 3 4],类型是[4]int,三个点代表自动推导长度,仍然是数组,a0并不是指向第一个元素的指针
	a1 := [6]int{3: 1, 2, 1: 3, 4} // [0 3 4 1 2 0],按索引下标赋初值
	a2 := [2][3]int{               // [2][3]int类型二维数组
		{0, 1, 2},
		{3, 4, 5},
	}
	fmt.Println(a0, a1, a2)

	/****************************** 切片 ******************************/
	// 切片是引用传递
	s0 := make([]int, 4, 6)       // 创建一个类型是[]int,长度为4,容量是6,初始默认值是0的切片,容量指重新切片时切片可以达到的最大长度,可省略
	fmt.Println(len(s0), cap(s0)) // 4 6
	fmt.Println(s0[:4], s0[3:])   // [0 0 0 0] [0],数组的cap值等于len值,S[A:B]范围是[A,B),跟python一样包含头不包含尾
	fmt.Println(s0[:6])           // [0 0 0 0 0 0],下标是否越界看下标是否超过其capacity值(切片,数组皆适用)
	//fmt.Println(s0[:7])           // error,最大不能超过cap值

	s1 := make([]int, 3, 4)
	s2 := s1[:2]                      // 切片的切片还是切片
	fmt.Println(s2, len(s2), cap(s2)) //  [0 0] 2 4

	s1 = append(s1, 1)
	s2[0]++
	fmt.Println(s1, s2) // [1 0 0 1] [1 0]

	s1 = append(s1, 2) // append引起s1指向的数组扩容产生了一个新数组,s2仍指向原来数组位置,同理如果append导致s2扩容,则也会与s1脱节
	s2[0]++
	fmt.Println(s1, s2) // [1 0 0 1 2] [2 0]

	var s3 []int // 等价于make([]int, 0) ,初始情况下len和cap都是0
	for i := 0; i < 10; i++ {
		// 当原切片长度小于1024时,新切片的容量会直接翻倍;当原切片的容量大于等于1024时,每次增加原容量的25%
		// 每次扩容后s3地址不变,但由于会新创建一个数组,所以切片内部的指针变量的值会随着扩容而改变
		s3 = append(s3, i)
		fmt.Printf("%p, %p, %p, cap: %d\n", &s3, &s3[0], s3, cap(s3)) // s3和&s3[0]都指向切片第一个元素的地址
	}

	s4 := []string{"round", "root", "世界", "cat"} // 未指定数组长度即为切片,等价于make([]string,4,4)并初始化
	s5 := make([]string, len(s4)-1)
	copy(s5, s4) // 切片深拷贝,如果s6长度不足,则会自动截取适当长度,返回拷贝的元素数量,数量等于min(len(src), len(dst))
	s5[0] = "circle"
	fmt.Println(s5)                 // [circle root 世界]
	s6 := append(s4[:1], s4[2:]...) // 由于追加的数据s4[2:]...未超过s4的容量,所以会直接影响到s4
	fmt.Println(s4, s6)             // [round 世界 cat cat] , [round 世界 cat] 思考这个结果
	_ = append(s4, "another")       // 如果基于s4继续追加的话,由于超过容量,产生一个新数组,此时s4不会被更改,基于这个原因一般使用形式是s=append(s,value)

	s7 := []int{6, 21, 1, 84, 3, 57}
	sort.Slice(s7, func(i, j int) bool {
		return s7[i]%10 < s7[j]%10 // 从小到大排序,按条件为真的顺序排序
	})
	fmt.Println(s7) // [21 1 3 84 6 57]
}

func main() {
	//a := 1.2
	//fmt.Println(testFunction(&a, false)) // [3] true, &意思是取地址

	//testString()
	//testDefinition()
	//testDefer()
	testSlice()
}
