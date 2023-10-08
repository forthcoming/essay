package main

import "fmt"

type Person[T int | float64] struct { // 范型类
	Name string
	Sex  T
}

type Number interface { // 也是一种接口
	~int64 | float64 // ~意思是支持int64所有衍生类型,即包括自定义类型
}

func SumIntOrFloat[K comparable, V Number](m map[K]V) V {
	// comparable约束表示可比较的类型(支持==和!=操作符),SumIntOrFloat[K comparable, V int64 | float64](m map[K]V)
	var s V
	for _, v := range m {
		s += v
	}
	return s
}

func main() {
	map1 := map[string]int64{
		"first":  34,
		"second": 12,
	}

	type myInt int64
	map2 := map[string]myInt{
		"first":  34,
		"second": 12,
	}

	map3 := map[string]float64{
		"first":  35.98,
		"second": 26.99,
	}

	fmt.Println(SumIntOrFloat[string, int64](map1), SumIntOrFloat[string, float64](map3))
	fmt.Println(SumIntOrFloat(map1), SumIntOrFloat(map2), SumIntOrFloat(map3)) // 自动推导范型类型

	person := Person[float64]{
		Name: "avatar",
		Sex:  1.7,
	}
	fmt.Println(person)
}
