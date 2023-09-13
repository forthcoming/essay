package main

import (
	"fmt"
	"math/rand"
	"os"
	"strconv"
	"time"
)

/*
When declaring an empty slice, prefer
var t []string
over
t := []string{}
The former declares a nil slice value, while the latter is non-nil but zero-length. They are functionally equivalent—their len and cap are both zero—but the nil slice is the preferred style.
Note that there are limited circumstances where a non-nil but zero-length slice is preferred, such as when encoding JSON objects (a nil slice encodes to null, while []string{} encodes to the JSON array []).
When designing interfaces, avoid making a distinction between a nil slice and a non-nil, zero-length slice, as this can lead to subtle programming errors.
*/

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

	testValue1 := 1
	fmt.Println(Count(testValue1, 2, 3), testValue1) // testValue1的值不会被Count改变
	testValue2 := []int{2, 3, 4}
	fmt.Println(Count(testValue2...), testValue2) // ...类似于python的解引用,可以不给Count传参,testValue2的值会被Count改变

	userFile := "note.txt"
	fOut, _ := os.OpenFile(userFile, os.O_RDWR|os.O_CREATE, 0666)
	defer fOut.Close()
	for i := 0; i < 5; i++ {
		_, _ = fOut.WriteString("write string!\n")
		_, _ = fOut.Write([]byte("write byte!\n"))
	}

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
		    	%p : 地址
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

	//dict := make(map[string]interface{}, 3)     // 只能指定容量,可以提高效率(不指定就自动扩容),没法像切片那样指定长度或容量
	time.Sleep(2 * time.Second)
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
