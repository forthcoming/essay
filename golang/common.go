package main

import (
	"encoding/json"
	"fmt"
	"math"
	"math/rand"
	"os"
	"reflect"
	"sort"
	"strconv"
	"strings"
	"time"
	"unicode/utf8"
	"unsafe"
	//lib "aaa"  导入包并起别名,导入的是目录的名字,通过 包名.object 访问包下面的公共对象,一般最后一个目录名和包名相同
	//_ "aaa"  匿名导入包,无法使用包里的内容,但能执行包里的init函数
	// main包不能被其他包导入,如果包A入包B,包B又导入包A,就会报错(import cycle not allowed)
	// 同一个目录下的文件的包名必须一致,目录下面可以再包含目录
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
go mod tidy # 清理不用的包,下载需要的包（直接go run也会自动下载依赖的包）
go env -w GOPROXY=https://goproxy.cn,direct  # 解决国内包同步问题
go env # 查看变量配置
go build hello.go 把go的源文件编译并且和它所依赖的包打包成可执行文件
go run -race hello.go 执行go代码(不打包),race会对代码做竞争检测
go build -gcflags "-N -l -S" 1.go # 编译Go文件生成汇编代码,-N禁止编译优化,-l禁止内联,-S打印汇编,-m显示变量是在堆还是栈分配
go tool objdump -S [-s symregexp] binary  # 反汇编可执行文件,-S在汇编旁边打印出Go源码,-s仅反汇编名称与正则表达式匹配的符号
go tool objdump binary start end  # 会从起始地址开始反汇编二进制文件,并在结束地址处停止

常量不能用于取地址符
c, d = d, c   // 交换两个变量的值
函数,结构体,映射,切片,指针,接口,信道的零值是nil
声明变量后若不赋值,使用默认值
类名,属性名,方法名首字母大写表示其他包和本包可以访问,否则只能在本包内访问
go语言不支持隐式类型转换
循环只有for关键字,针对数组切片遍历的是索引+值,针对map遍历的是key+value
++,--只支持后置操作
函数不支持默认参数
机器指令是由0和1组成的二进制指令,汇编语言是二进制指令的文本形式,与机器指令一一对应,比如加法的机器指令是00000011写成汇编语言就是ADD

单元测试注意点: 文件名必须是xxx_test格式; 测试函数名必须是TestXxx格式; 入参必须是t *testing.T
func TestPrint(t *testing.T) {
	fmt.Println("in testPrint")
}

make用来为slice,map,chan类型分配内存和初始化一个对象,返回的是引用类型
new可以初始化任意对象,返回的是对象指针,不建议用来new引用类型,因为仅仅为引用的对象名分配空间,对象名此时仍然指向nil,new不常用

可以给内置类型如int增加方法,前提是用type给int定义命名类型(type MyInt int),MyInt和int不再是相同类型
type AliasInt=int给int起别名,AliasInt和int是相同类型
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
	// ``代表多行字符串
	str := "AB中C"                  // 字符串底层是一个byte数组,因此string也可以进行切片处理,字符串是不可变对象,无法被修改
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

	fmt.Println("Hello" + " World!")
	strings.Contains("seafood", "foo")                // true
	strings.Join([]string{"foo", "bar", "baz"}, ", ") // foo, bar, baz
	strings.Index("chicken", "ken")                   // 4, substr不存在返回-1
	strings.Split("a,b,c", ",")                       // [a b c]
	strings.Replace("oink oink oink", "o", "l", 2)    // link link oink, n表示替换的次数,小于0表示全部替换

	// 字符串与其他类型互转
	fmt.Println(strconv.FormatBool(false), strconv.FormatInt(1234, 10))
	myBool, _ := strconv.ParseBool("false")
	myFloat, _ := strconv.ParseInt("111", 2, 64) // 7
	fmt.Println(myBool, myFloat)
}

func testDefinition() {
	var a int // int类型默认初始值为0, var可以初始化全局变量
	fmt.Println("a=", a, math.MinInt, math.MaxInt, unsafe.Sizeof(a))

	b := "hello"        // 自动类型推导为string, :=操作符要求至少有一个变量尚未声明,不能初始化全局变量
	b, c := "world", 50 // b已经声明,但c尚未声明
	b, c = "oracle", 90 // 给已经声明的变量b和c赋新值
	fmt.Println("changed b is", b, "c is", c)
}

func testFunction(a *float64, b bool) ([]int, bool) { // 单个返回值不用()
	// 所有参数都是值传递,函数可以作为变量的值,可以作为参数和返回值
	// func name() (a, b int, c bool) { return }  返回值可以带上变量名,函数结束直接return即可,相同类型返回值可以合并声明
	*a += 1
	multiPointer := &a // multiPointer类型为**float64
	**multiPointer += 1
	return []int{int(*a)}, !b
}

func testClosure() func(int) int {
	x := 0 // moved to heap: x
	return func(y int) int {
		x += y
		return x
	}
}

func testShadowDeclaration() (str string) {
	if true {
		//str = "inner"
		//return     // 正确,如果return后不接变量,则返回的始终是返回值列表中的变量

		str := "inner"
		fmt.Println(str)
		return str // 正确,return后必须加上变量名 输出inner
	}
	return
}

func testVariableParam(values ...int) int { // 可变参数
	// values是[]int类型,且入参只能是int型切片的解引用或多个int型参数
	total := 0
	fmt.Printf("values's type is %T, cap: %d, len: %d\n", values, cap(values), len(values)) // []int
	for _, val := range values {
		total += val
	}
	values[0] = 100              // 由于是切片传参,此处会直接影响到入参值
	values = append(values, 200) // append引起values扩容,指向了新位置,所以append不会影响到入参值
	return total
}

func testArray() {
	// 数组是值传递
	// 数组是否相等前提是类型相同,[2]int和[1]int被认为是不同类型,切片只能跟nil做比较
	// 数组的cap值等于len值且不可被更改,无法用于append
	a0 := [...]int{1, 2, 3, 4}     // [1 2 3 4],类型是[4]int,三个点代表自动推导长度,仍然是数组,a0并不是指向第一个元素的指针
	a1 := [6]int{3: 1, 2, 1: 3, 4} // [0 3 4 1 2 0],按索引下标赋初值
	a2 := [2][3]int{               // [2][3]int类型二维数组
		{0, 1, 2},
		{3, 4, 5},
	}
	fmt.Println(a0, a1, a2)
	fmt.Println(unsafe.Sizeof(a0))      // 32,计算的是所有元素大小之和
	fmt.Printf("%p, %p\n", &a0, &a0[0]) // &a0和&a0[0]都指向数组第一个元素的地址

	eleSize := unsafe.Sizeof(a0[0])
	uintPtr := uintptr(unsafe.Pointer(&a0[0]))              // 将*int类型转换为无符号整数
	fmt.Println(*(*int)(unsafe.Pointer(uintPtr + eleSize))) // 2

	a3 := &a0
	a3[0] = 0       // 注意这里不用加*,结构体有类似写法,加*正确写法是(*a3)[0] = 0
	fmt.Println(a0) // [0 2 3 4]
}

func testSlice() {
	// 切片是引用传递
	// make返回的都是引用类型,创建一个类型是[]int,长度为4,容量是6,初始默认值是0的切片,容量指切片扩容前可达到的最大长度,可省略,此时cap=len
	s0 := make([]int, 4, 6)        // 申请unsafe.Sizeof(s0[0]) * cap个字节,在32位平台上int类型占4字节,在64位平台上占用8字节
	fmt.Println(len(s0), cap(s0))  // 4 6
	fmt.Println(unsafe.Sizeof(s0)) // 一般为24,由8bit cap + 8bit len + 8bit pointer构成
	fmt.Println(s0[:6])            // [0 0 0 0 0 0],下标是否越界看下标是否超过其capacity值(切片,数组皆适用)
	//fmt.Println(s0[:7]) // error,最大不能超过cap值
	//fmt.Println(s0[4])           // error,必须小于len值

	s1 := make([]int, 3, 4)
	s2 := s1[:2]                      // 切片的切片还是切片,S[A:B]范围是[A,B),跟python一样包含头不包含尾,但不能是负数
	fmt.Println(s2, len(s2), cap(s2)) //  [0 0] 2 4, cap(S[A:B]) = cap(S) - A

	s1 = append(s1, 1)
	s2[0]++
	fmt.Println(s1, s2) // [1 0 0 1] [1 0]

	s1 = append(s1, 2) // append引起s1指向的数组扩容产生了一个新数组,s2仍指向原来数组位置,同理如果append导致s2扩容,则也会与s1脱节
	s2[0]++
	fmt.Println(s1, s2) // [1 0 0 1 2] [2 0]

	var s3 []int
	for i := 0; i < 10; i++ {
		// 当原切片长度小于1024时,新切片的容量会直接翻倍;当原切片的容量大于等于1024时,每次增加原容量的25%
		// s3和&s3[0]始终指向切片第一个元素的地址,每次扩容后s3地址不变,但由于会创建新数组,s3的值会随着扩容而改变
		s3 = append(s3, i)
		fmt.Printf("%p, %p, %p, cap: %d\n", &s3, &s3[0], s3, cap(s3))
	}

	s4 := []string{"round", "root", "世界", "cat"} // 未指定数组长度即为切片,等价于make([]string,4,4)并初始化
	s5 := make([]string, len(s4)-1)
	copy(s5, s4) //  [round root 世界],切片深拷贝,如果s5长度不足,则会自动截取适当长度,返回拷贝的元素数量,数量等于min(len(src), len(dst))

	s6 := append(s4[:1], s4[2:]...) // 由于追加的数据s4[2:]...未超过s4的容量,所以会直接影响到s4
	fmt.Println(s4, s6)             // [round 世界 cat cat] , [round 世界 cat] 思考这个结果
	_ = append(s4, "another")       // 如果基于s4继续追加的话,由于超过容量,产生一个新数组,此时s4不会被更改,基于这个原因一般使用形式是s=append(s,value)

	s7 := []int{6, 21, 1, 84, 3, 57}
	sort.Slice(s7, func(i, j int) bool {
		return s7[i]%10 < s7[j]%10 // 从小到大排序,按条件为真的顺序排序
	})
	fmt.Println(s7) // [21 1 3 84 6 57]

	// 声明空切片时优先选择var t []int而不是t := []int{},前者声明一个nil切片值,后者等价于make([]int, 0, 0),非nil但长度为零的切片,它们的len和cap都为零
	// 在编码JSON对象时nil切片编码为null,[]int{}编码为数组[]
	// 设计接口时避免区分nil切片和非nil零长度切片,因为这可能导致微妙的编程错误
	var z []int
	y := make([]int, 0)
	fmt.Printf("%T,%T\n", y, z)                     // []int,[]int
	fmt.Println(len(y), len(z), y != nil, z == nil) // 0 0 true true
	for idx, value := range z {                     // 遍历y,z都不会报错
		fmt.Println(idx, value)
	}

	// 二维切片初始化, ySize行xSize列
	xSize, ySize := 5, 10
	picture := make([][]uint8, ySize)
	for i := range picture { // 遍历行,为每一行分配切片
		picture[i] = make([]uint8, xSize)
	}
}

func testMap() {
	myMap := map[int]string{ // Map无序,是引用操作
		22: "sun",
		33: "avatar", // 一行赋值时结尾不用逗号
	}
	//var myMap map[int]string
	//myMap := make(map[string]interface{}, 3) // 只能指定容量,可以提高效率(不指定就自动扩容),没法像切片那样指定长度和容量
	myMap[11] = "\"oracle\"" // 转义字符
	name, ok := myMap[11]
	fmt.Println(name, ok) // "oracle" true ,访问不存在的key会返回默认值,ok是False
	delete(myMap, 22)     // 删除不存在的key不会报错
	for key, value := range myMap {
		println(key, value)
	}

	m := map[string]struct{ x int }{
		"foo": {2},
	}
	//m["foo"].x = 4  // error
	tmp := m["foo"]
	tmp.x = 4
	m["foo"] = tmp
	// 如果不想利用tmp,可以如下定义
	//m := map[string]*struct{ x int }{
	//	"foo": {2},
	//}
}

func testSwitch() {
	local := 15
	switch local { // switch-case会按照case定义顺序逐个判断是否满足条件,若switch后面没有表达式,它将匹配true(相当于if-else-if-else)
	case 15:
		fmt.Println("111")
		fallthrough // 强制执行后一个case语句块
	case 20:
		fmt.Println("222") // 不需要加break
	case 1, 2:
		fmt.Println("333")
	default:
		fmt.Println("default")
	}
}

func testTime() {
	// 秒             毫秒                 微秒                 纳秒
	// Second = 1e3 * Millisecond = 1e6 * Microsecond = 1e9 * Nanosecond = 1e9
	queryTime := time.Date(2021, 4, 1, 0, 0, 0, 0, time.Local)
	queryTime = queryTime.AddDate(0, -1, 0)
	fmt.Println(queryTime.Unix(), queryTime.UnixNano()) // Unix返回秒级整形时间戳,UnixNano返回纳秒级整形时间戳

	// Add是给现有时间加减分钟或者小时
	before := queryTime.Add(-2 * time.Second)
	// Sub是前一个时间减后一个时间的时差,before - queryTime, 返回time.Duration类型
	duration := before.Sub(queryTime)
	fmt.Println(duration, duration < 0) // -2s true

	// 记忆诀窍: 2006年12345,也可以2006-01-02 03:04:05但有区别
	fmt.Println(time.Now().Format("2006-01-02 15:04:05"))                                       // 2023-09-14 20:03:40
	fmt.Println(time.Now().Format("03:04:05"))                                                  // 08:03:4
	fmt.Println(time.Unix(time.Now().Unix(), 0))                                                // 将时间戳转换为时间
	fmt.Println(time.ParseInLocation("2006-01-02 15:04:05", "2021-01-21 14:30:00", time.Local)) // 字符串转时间

	time.Sleep(2 * time.Second)
}

func testPrint() {
	/*
					%b : 二进制
					%c : 字符
					%d : 整数
					%f : 浮点数
		            %% : 百分号
					%t : bool类型
			    	%p : 地址
					%s : 字符串
					%T : 变量类型, reflect.TypeOf(args)
					%v : 默认格式输出(通用输出格式),%+v会为结构体的每个字段添上字段名,%#v按照Go语法打印值
	*/
	// 04意思是长度为4,不足的前面用0补齐;返回[0,5)范围内伪随机整数,使用前一定要重置随机种子(py会自动执行这一步),%可通过%%进行转意
	formatString := fmt.Sprintf("%04d", rand.Intn(5)) // sprintf是格式化字符串给变量,printf是格式化字符串打印出来
	fmt.Println(formatString)
	fmt.Printf("%v,%T", 2, 2) // 2,int
}

func testOpenFile() {
	fOut, _ := os.OpenFile("test_open_file.txt", os.O_RDWR|os.O_CREATE, 0666)
	defer fOut.Close()
	for range 3 { //  for _ := range 3
		_, _ = fOut.WriteString("write string!\n")
		_, _ = fOut.Write([]byte("write byte!\n"))
	}
}

func testReflect() {
	data := map[string]any{
		"name": "sakura",
		"age":  12,
	}

	info := struct {
		Sex         int    `yaml:"sex"`
		PhoneNumber string `yaml:"phone_number"`
	}{
		1,
		"13189616789",
	}
	//TypeOf: 用来获取输入参数接口中的值的类型, 如果接口为空则返回nil
	infoType := reflect.TypeOf(info) // 此处必须传值类型
	//ValueOf: 用来获取输入参数接口中的数据的值, 如果接口为空则返回0
	infoValue := reflect.ValueOf(info) // 此处必须传值类型
	if infoValue.Kind() == reflect.Struct {
		fmt.Println("是结构体")
	}

	for idx := 0; idx < infoValue.NumField(); idx++ { // 按照结构体定义成员变量的顺序遍历
		valueFiled := infoValue.Field(idx)
		typeFiled := infoType.Field(idx) // 拥有typeFiled.Name,typeFiled.Type,typeFiled.Tag等属性
		tag := typeFiled.Tag.Get("yaml")
		data[tag] = valueFiled.Interface() // 无法返回私有变量的值
	}
	dataByte, _ := json.Marshal(data)
	fmt.Println(string(dataByte))

	for idx := 0; idx < infoType.NumMethod(); idx++ {
		method := infoType.Method(idx)
		fmt.Println(method.Name, method.Type)
	}
}

func nextslicecap(newLen, oldCap int) int { // slice扩容源代码,参考https://github.com/golang/go/blob/master/src/runtime/slice.go
	// newLen = new length (= oldLen + num)
	// oldCap = original slice's capacity.
	// num = number of elements being added
	// newCap = capacity of the new backing store
	// Requires that uint(newLen) > uint(oldCap) and assumes the original slice length is newLen - num
	newcap := oldCap
	doublecap := newcap + newcap
	if newLen > doublecap {
		return newLen // 会被roundupsize修正
	}

	const threshold = 256
	if oldCap < threshold {
		return doublecap
	}
	for {
		// Transition from growing 2x for small slices
		// to growing 1.25x for large slices. This formula
		// gives a smooth-ish transition between the two.
		newcap += (newcap + 3*threshold) >> 2

		// We need to check `newcap >= newLen` and whether `newcap` overflowed.
		// newLen is guaranteed to be larger than zero, hence
		// when newcap overflows then `uint(newcap) > uint(newLen)`.
		// This allows to check for both with the same comparison.
		if uint(newcap) >= uint(newLen) {
			break
		}
	}

	// Set newcap to the requested cap when the newcap calculation overflowed.
	if newcap <= 0 {
		return newLen
	}
	return newcap
}

func main() { // 程序开始执行的函数,名字main固定,{不能单独一行
	//a := 1.2
	//fmt.Println(testFunction(&a, false)) // [3] true, &意思是取地址
	//fmt.Println(testVariableParam([3]int{2, 3, 4}...)) // error
	//vValue := 1
	//fmt.Println(testVariableParam(vValue, 2, 3), vValue) // vValue的值不会被testVariableParam改变
	//vValue1 := []int{2, 3, 4}                            // len(vValue1)=cap(vValue1)=3
	//fmt.Println(testVariableParam(vValue1...), vValue1)  // ...类似于python的解引用,vValue1的值会被testVariableParam改变

	//f := testClosure()
	//fmt.Println(f(10), f(10)) // 10 20

	//testString()
	//testDefinition()
	testArray()
	//testSlice()
	//testMap()
	//testSwitch()
	//testTime()
	//testPrint()
	//testOpenFile()
	//testReflect()
}
