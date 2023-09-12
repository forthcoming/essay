package test

import (
	format "fmt"
	"strconv"
) // 给包起别名
// import 默认从GOPATH下面的src开始导入
// import "testmodule/foo" 导入时，是按照目录导入。导入目录后，可以使用这个目录下的所有包,出于习惯，包名和目录名通常会设置成一样，所以会让你有一种你导入的是包的错觉
// 同一个目录下的文件的包名必须一致，目录下面可以再包含目录
// main包不能被其他包导入,如果包A入包B,包B又导入包A,就会报错(import cycle not allowed)
// 只要是导入了某个包,其包内的所有公共函数,变量都可以通过 包.object 方式调用


type INT int32

func mai1n(){

	stringInt := strconv.FormatInt(7,2)
	format.Println(stringInt)   // 111



	//var age INT = 6
	//format.Println(age,unsafe.Sizeof(age),reflect.TypeOf(age))

	// 类型不匹配
	//var score int32 = 4
	//score+age

	// make返回的是引用类型,new返回的是指针类型
	//makeMap := make(map[int]string)
	//newMap := new(map[int]string)
	//format.Println(reflect.TypeOf(makeMap),reflect.TypeOf(newMap))

	//chan1 := make(chan int)
	//chan2 := make(chan bool)
	//for{
	//	select{
	//	    case num := <-chan1:
	//		    format.Printf("number is %d",num)
	//		case num1 := <-chan2:
	//            format.Printf("number is %t",num1)
	//    }
	//}


	//c := make(chan bool)
	//for i := 0; i < 100; i++ {
	//   go func(i int) {
	//   	format.Println(i)
	//   	c <- true
	//   }(i)
	//}  // 为什么不是死锁
}


//https://mp.weixin.qq.com/s?__biz=MzU1NzU1MTM2NA==&mid=2247483782&idx=1&sn=d86f90b98e3c095e71d8a333a9b50d4f&chksm=fc355bedcb42d2fbb1a15ab5b7be4fee284d26d32a6fea4cf37d9b6d9679e5c240b9acb89b89&scene=21#wechat_redirect
