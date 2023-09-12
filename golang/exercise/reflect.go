package main

import (
	"encoding/json"
	"fmt"
	"reflect"
)

/*
TypeOf: 用来获取输入参数接口中的值的类型, 如果接口为空则返回nil
ValueOf: 用来获取输入参数接口中的数据的值, 如果接口为空则返回0
*/

type Info struct {
	Sex         int    `yaml:"sex"`
	PhoneNumber string `yaml:"phone_number"`
}

func test1() {
	info := Info{1, "13189616789"}
	data := map[string]interface{}{
		"name": "sakura",
		"age":  12,
	}

	infoType := reflect.TypeOf(info)                  // 此处必须传值类型
	infoValue := reflect.ValueOf(info)                // 此处必须传值类型
	for idx := 0; idx < infoValue.NumField(); idx++ { // 按照结构体定义成员变量的顺序遍历
		typeFiled := infoType.Field(idx)
		// typeFiled.Name
		// typeFiled.Type
		tag := typeFiled.Tag.Get("yaml")
		valueFiled := infoValue.Field(idx)
		data[tag] = valueFiled.Interface() // cannot return value obtained from unexported field or method
	}
	dataByte, _ := json.Marshal(data)
	fmt.Println(string(dataByte))
}

func main() {
	test1()
}
