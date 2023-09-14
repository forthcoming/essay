package main

import (
	"fmt"
	"math/rand"
	"os"
	"strconv"
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

func main() {
	shadowedTest()

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
				%T : 变量类型, reflect.TypeOf(args)
				%v : 默认格式输出(通用输出格式)
	*/
	formatString := fmt.Sprintf("%04d", rand.Intn(5)) // 04意思是长度为4,不足的前面用0补齐;返回[0,5)范围内伪随机整数,使用前一定要重置随机种子(py会自动执行这一步)
	fmt.Println(formatString)
}
