package main

import (
	"sync"
)

var once sync.Once
var mutex sync.Mutex
var done uint32

type example struct {
	name string
}

var instance *example

// 懒汉模式
func GetInstance0() *example {
	// 存在线程安全问题,高并发时有可能创建多个对象
	if instance == nil {
		instance = &example{}
	}
	return instance
}

// 饿汉模式
// 在包加载的时候就创建单例对象(实例初始化放在包init函数中执行, 实例化单例)
// 和懒汉模式相比,更安全, 但当程序中用不到该对象时浪费了部分空间, 减慢程序启动速度

// 双重检查机制(Check-lock-Check), 也叫DCL(Double Check Lock)
func GetInstance1() *example {
	if instance == nil { // 单例没被实例化才会加锁
		mutex.Lock()
		defer mutex.Unlock()
		if instance == nil { // 单例没被实例化才会创建(注意此处要再判断一次)
			instance = &example{}
		}
	}
	return instance
}

// Go特有实现(推荐)
func GetInstance2() *example {
	once.Do(func() { // Do方法保证在程序运行过程中只运行一次其中的回调
		instance = &example{}
	})
	return instance

	// 等价代码
	//if atomic.LoadUint32(&done) == 0{
	//	mutex.Lock()
	//	defer mutex.Unlock()
	//	if done == 0 {
	//		defer atomic.StoreUint32(&done, 1)  // 原子装载
	//		instance = &example{}
	//	}
	//}
	//return instance
}
