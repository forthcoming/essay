package test_test

import (
	"fmt"
	"testing"
)


// 单元测试注意点:
// 文件名必须是xxx_test格式
// 测试函数名必须是TestXxx格式, 入参必须是t *testing.T
func TestPrint(t *testing.T) {
	fmt.Println("in testPrint")
}

