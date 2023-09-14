package main

import (
	"encoding/json"
	"fmt"
	"gopkg.in/yaml.v3"
)

type Book struct {
	/*
				如果结构体包含不可比较的字段,则该结构体实例间也不可比较; 如果它的每一个字段都可比较,则该结构体实例间也可比较(==和!=)
				如果函数返回值定义了结构体指针变量,则该变量是空指针类型
				名为S的结构体不能再包含S类型的成员,但可以包含*S指针类型的成员
			    可以给内置类型如int增加方法,前提是用type给int定义命名类型
		        可变参数可以用结构体指针,这样如果使用者不想传,可以直接用空指针
	*/
	title  string
	author string
	bookId int
	next   *Book
}

func testCommon() {
	book1 := Book{"C++", "sakura", 1, nil} // 初始化要么全用key-value形式,要么全用value形式,后者只能按成员声明顺序一一赋值
	book2 := Book{title: "Go", bookId: 2}  // 忽略的字段用默认值
	book3 := new(Book)                     // 等价于 book3 := &Book{}
	var book4 Book                         // 等价于 book4 := Book{}

	var book5 *Book // 此时book5还是nil的空指针,未分配实际内存
	// book5.bookId = 5     // 错误写法, 当结构体指针为nil时只能被赋一个拥有实际存储地址的结构体指针后,才能访问自己的成员变量
	book5 = book3
	book5.title = "Python" // 结构体指针访问成员方式跟结构体变量一样
	fmt.Println(book1, book2, book3, book4)

	employee := struct {
		firstName, lastName string
		age                 int
	}{
		firstName: "Lucas",
		lastName:  "Nikola",
		age:       31,
	}
	fmt.Println("匿名结构体", employee)
}

func testReverse() {
	book1 := []Book{
		{"C++", "sakura", 12, nil},
		{"Go", "neo", 22, nil},
	}
	var book1Ptr []*Book
	for _, book := range book1 {
		book.bookId /= 2                   // 此处book是值拷贝,不会影响到book1
		book1Ptr = append(book1Ptr, &book) // 错误写法,应为遍历过程中book的地址始终不变,只有值在变
	}
	fmt.Println(book1, book1Ptr) // [{C++ sakura 12 <nil>} {Go neo 22 <nil>}] [0xc0001080c0 0xc0001080c0]

	book2 := book1
	for idx := range book2 {
		book2[idx].bookId /= 2 // 由于book1是切片,因此改变book2会影响到book1
	}
	fmt.Println(book1)

	book3 := []*Book{
		{"C++", "sakura", 12, nil},
		{"Go", "neo", 22, nil},
	}
	var book3Ptr []*Book
	for _, book := range book3 {
		book.bookId /= 2                  // 此处book是指针的值拷贝,会影响到book3
		book3Ptr = append(book3Ptr, book) // 正确写法
	}
	fmt.Println(book3, book3Ptr)
}

func testJsonMarshal() {
	type JsonExt struct {
		Friend string
		Number int
	}
	type JsonData struct {
		// omit 美[əˈmɪt]  v. 省略; 忽略; 遗漏; 删除; 漏掉
		// 重命名json序列化后的字段名,omitempty属性只要发现字段值为false,0,空指针,空接口,空数组,空切片,空映射,空字符串中的一种,就会被忽略
		Name     string `json:"name,omitempty"`
		nickname string `json:"nick_name"` // 小写开头的变量无法在其他包中被访问,因此被忽略
		Age      int32  `json:"-"`         // -意思是忽略
		Scores   []int  // 不指定别名则按照原始字段序列化
		JsonExt
		Ext     JsonExt
		Mapping map[int]string // struct和map序列化后的形式一样
	}

	jsonSource := JsonData{
		"welcome",
		"oracle",
		12,
		[]int{1, 2},
		JsonExt{"zgt", 10},
		JsonExt{"newer", 20},
		map[int]string{1: "A", 4: "B"},
	}
	/*
		{
		    "name":"welcome",
		    "Scores":[1,2],
		    "Friend":"zgt",
		    "Number":10,
		    "Ext":{"Friend":"newer","Number":20},
		    "Mapping":{"1":"A","4":"B"}
		}
	*/
	jsonTarget, _ := json.Marshal(jsonSource) // jsonTarget类型是[]uint8
	fmt.Println(string(jsonTarget))
	jsonSource = JsonData{}
	_ = json.Unmarshal(jsonTarget, &jsonSource)
}

func testYamlMarshal() {
	type YamlExt struct {
		Key   string `yaml:"key"`
		Array []any  `yaml:"array"`
	}
	type YamlData struct {
		Yaml      []string `yaml:"yaml"`
		Paragraph string   `yaml:"paragraph"`
		Object    YamlExt  `yaml:"object"`
	}
	// ``代表多行字符串
	yamlTarget := `
      yaml:
        - slim and flexible
        - better for configuration
      object:
        key: value
        array:
          - null_value:
            boolean: true  
          - integer: 1
      paragraph:
        Blank lines denote paragraph breaks
    `
	/*
		{
			"Yaml": ["slim and flexible", "better for configuration"],
			"Paragraph": "Blank lines denote paragraph breaks",
			"Object": {
				"Key": "value",
				"Array": [{
					"boolean": true,
					"null_value": null
				}, {
					"integer": 1
				}]
			}
		}
	*/

	yamlSource := YamlData{}
	_ = yaml.Unmarshal([]byte(yamlTarget), &yamlSource)
	jsonTarget, _ := json.Marshal(yamlSource)
	fmt.Println(string(jsonTarget))
}

func main() {
	//testCommon()
	//testReverse()
	//testYamlMarshal()
	testJsonMarshal()
}
