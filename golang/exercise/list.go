package main

import (
	"fmt"
	"sort"
)

// []string{""}和[]string{}长度不一样,但在用fmt.Println打印时显示的都是[]

func main() {
	/****************************** 数组 ******************************/
	// 数组是值传递
	a0 := [...]int{1, 2, 3, 4}     // [1 2 3 4] ; 三个点代表自动推导长度,仍然是数组,a0并不是指向第一个元素的指针
	a1 := [6]int{3: 1, 2, 1: 3, 4} // [0 3 4 1 2 0] ; 按索引下标赋初值
	a2 := [2][3]int{               // 二维数组
		{0, 1, 2},
		{3, 4, 5},
	}
	fmt.Println(a0, a1, a2)
	/****************************** 数组 ******************************/

	/****************************** 切片 ******************************/
	// 切片是引用传递
	//dict := make(map[string]interface{}, 3)                 // 只能指定容量,可以提高效率(不指定就自动扩容),没法像切片那样指定长度或容量
	s1 := make([]int, 3, 4)                                 // 创建一个长度为3,初始默认值是0的切片,容量是4,容量指the maximum length the slice can reach when resliced
	s2 := s1[:2]                                            // 切片的切片还是切片
	fmt.Println(s1, len(s1), cap(s1), s2, len(s2), cap(s2)) // [0 0 0] 3 4 [0 0] 2 4
	s1 = append(s1, 1)
	s2[0]++
	fmt.Println(s1, s2) // [1 0 0 1] [1 0]
	s1 = append(s1, 2)  // append引起了s1指向的数组扩容产生了一个新数组,s2仍指向原来数组位置,同理如果append导致s2扩容,则也会与s1脱节
	s2[0]++
	fmt.Println(s1, s2) // [1 0 0 1 2] [2 0]

	var s3 []int // 初始情况下len和cap都是0
	for i := 0; i < 10; i++ {
		// 当原切片长度小于1024时,新切片的容量会直接翻倍;当原切片的容量大于等于1024时,会反复地增加25%直到新容量超过所需要的容量
		// 每次扩容后s3地址不变,但由于会新创建一个数组,所以切片内部的指针变量的值会随着扩容而改变
		s3 = append(s3, i)
		fmt.Printf("%p, %p, %p ,%v, len: %d, cap: %d\n", &s3, &s3[0], s3, s3, len(s3), cap(s3)) // %p是打印地址,s3就代表切片第一个元素的地址值,即s3和&s3[0]指向相同地址
	}

	s4 := []string{"google", "root", "世界", "cat"} // 未指定数组长度的其实定义的是切片
	s5 := s4                                      // 切片是引用操作
	s5[0] = "round"
	s6 := make([]string, len(s4)-1)
	copy(s6, s4) // 切片深拷贝,如果s6长度不足,则会自动截取适当长度; Copy returns the number of elements copied, which will be the minimum of len(src) and len(dst).
	s6[0] = "circle"
	fmt.Println(s6, len(s4), cap(s4), s4[:2], s4[2:], s4[1:3]) // 包含头不包含尾,跟python一样

	fmt.Println(s4)                 // [round root 世界 cat]
	s7 := append(s4[:1], s4[2:]...) // 由于追加的数据s4[2:]...未超过s4的容量,所以会直接影响到s4
	fmt.Println(s4, s7)             // [round 世界 cat cat] , [round 世界 cat] 思考这个结果
	_ = append(s4, "another")       // 如果基于s4继续追加的话,由于超过容量,产生一个新数组,此时s4不会被更改,基于这个原因一般使用形式是s=append(s,value)

	s8 := []int{6, 21, 1, 84, 3, 57}
	sort.Slice(s8, func(i, j int) bool {
		return s8[i]%10 < s8[j]%10 // 从小到大排序,按条件为真的顺序排序
	})
	fmt.Println(s8)
	/****************************** 切片 ******************************/

	/****************************** 下标越界 ******************************/
	// 下标是否越界主要是看下标是否超过其capacity值(切片,数组皆适用)
	// 数组的cap值等于len值,S[A:B]范围是[A,B)
	s9 := make([]int, 4, 6)       // 参数分别为类型,长度,容量,类型和长度必须指定
	fmt.Println(len(s9), cap(s9)) // 4,6
	fmt.Println(s9[:4])           // [0 0 0 0]
	fmt.Println(s9[3:])           // [0]
	fmt.Println(s9[:6])           // [0 0 0 0 0 0]
	//fmt.Println(s9[:7])  // error,最大不能超过cap值
	/****************************** 下标越界 ******************************/
}
