package main

import (
	"encoding/json"
	"fmt"

	"gopkg.in/yaml.v3"
)

type JsonExt struct {
	Friend string
	Number int
}

type JsonData struct {
	Name     string `json:"name,omitempty"` // 重命名json序列化后的字段名,omitempty属性只要发现字段值为false,0,空指针,空接口,空数组,空切片,空映射,空字符串中的一种,就会被忽略
	nickname string `json:"nick_name"`      // 小写开头的变量不会被序列化,应为结构体中小写开头的成员变量是私有变量,无法在其他包中被访问
	Age      int32  `json:"-"`              // -意思是不转换
	Scores   []int  // 不指定别名则按照原始字段序列化
	JsonExt
	Ext     JsonExt
	Mapping map[int]string // 注意struct和map序列化后的形式一样
}

type YamlExt struct {
	Key   string        `yaml:"key"`
	Array []interface{} `yaml:"array"`
}

type YamlData struct {
	Json      []string `yaml:"json"`
	Yaml      []string `yaml:"yaml"`
	Paragraph string   `yaml:"paragraph"`
	Object    YamlExt  `yaml:"object"`
}

func main() {
	jsonSource := JsonData{
		"welcome",
		"oracle",
		12,
		[]int{1, 2},
		JsonExt{"zgt", 10},
		JsonExt{"newer", 20},
		map[int]string{1: "A", 4: "B"},
	}
	jsonTarget, _ := json.Marshal(jsonSource) // jsonTarget类型是[]uint8
	fmt.Println(string(jsonTarget))           // {"name":"welcome","Scores":[1,2],"Friend":"zgt","Number":10,"Ext":{"Friend":"newer","Number":20},"Mapping":{"1":"A","4":"B"}}

	jsonSource = JsonData{}
	err := json.Unmarshal(jsonTarget, &jsonSource)
	fmt.Println(err, jsonSource, jsonSource.Name)

	/*
		    https://www.bejson.com/validators/yaml_editor/
			key => "key"
			key: => {"key": null}
			- key => ["key"]
	*/
	yamlSource := YamlData{}
	yamlTarget := `
json: 
  - rigid   # this is a comment,字符串一般不需要加引号,缩进会影响层级
  - better for data interchange
yaml:
  - slim and flexible
  - better for configuration
object:
  key: value
  array:
    - null_value:
      boolean: true    # 任何时候都需要以两个空格来缩进,不然会出错
    - integer: 1
paragraph:
  Blank lines denote paragraph breaks
`

	_ = yaml.Unmarshal([]byte(yamlTarget), &yamlSource)
	jsonTarget, _ = json.Marshal(yamlSource)
	fmt.Println(string(jsonTarget))
	/*
		{
			"Json": ["rigid", "better for data interchange"],
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
}
