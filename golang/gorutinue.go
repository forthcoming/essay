package main

import (
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

// 主协程退出,其他子协程也要跟着退出,Goroutine没有ID号

func testWaitGroup() {
	wg := sync.WaitGroup{} // WaitGroup传递要使用指针
	ch1 := make(chan int, 5)
	ch2 := make(chan int, 10)                       // 带缓存的channel
	fmt.Println("len:", len(ch2), "cap:", cap(ch2)) // len: 0 cap: 10

	wg.Add(2)
	go func(ch1 chan<- int, wg *sync.WaitGroup) { // 可以定义单向通道的channel,双向通道可以作为单向通道的入参
		defer wg.Done()
		//runtime.Goexit() // 退出当前协程
		for i := 0; i < 5; i++ {
			ch1 <- i
		}
		close(ch1) // 用完关闭,防止下面协程死锁,通道关闭后可以一直取默认值,且第二个参数是false,无法向关闭的通道中发送数据
	}(ch1, &wg)
	go func(ch1 <-chan int, ch2 chan<- int, wg *sync.WaitGroup) { // 单向通道,限定通道方向
		defer wg.Done()
		for i := range ch1 {
			ch2 <- i * i
		}
		close(ch2)
	}(ch1, ch2, &wg)
	wg.Wait()

	for ret := range ch2 {
		fmt.Println(ret)
	}
	//for {  // 死循环
	//	if ret, ok := <-ch2; ok {
	//		fmt.Println(ret)
	//	} else {
	//		break
	//	}
	//}
}

func testRaceCondition() {
	var atomicCounter int32 = 0
	lockCounter := 0
	lock := sync.Mutex{} // 互斥锁,传递要使用指针
	wg := sync.WaitGroup{}
	for i := 0; i < 99999; i++ {
		wg.Add(1) // 一定要在Wait函数执行前执行
		go func(lock *sync.Mutex, wg *sync.WaitGroup) {
			atomic.AddInt32(&atomicCounter, 1) // 效率比锁更高
			lock.Lock()
			defer lock.Unlock()
			defer wg.Done() // 等价于wg.Add(-1)
			lockCounter++
		}(&lock, &wg)
	}
	wg.Wait() // 会阻塞代码的运行,直到计数器值减为0
	fmt.Println("atomicCounter:", atomicCounter, "lockCounter", lockCounter)

	mapping := sync.Map{} // 该map并发安全,读写通过Load和Store实现,key-value类型可以不同
	mapping.Store("key", "value")
	mapping.Store(1, 2)
}

func testSelect() {
	ch := make(chan int)
	stop := make(chan bool)                           // 不带缓冲的channel
	fmt.Println("len:", len(stop), "cap:", cap(stop)) // len: 0 cap: 0

	go func() {
		for j := 0; j < 30; j++ {
			ch <- j
		}
		stop <- true
	}()
	for run := true; run; {
		select { // 同时处理多个channel,case执行顺序随机
		//case ch <- 1: // 如果成功向ch写入数据,则执行对应case处理语句
		case _ = <-stop:
			run = false
			break // 应为break仅仅退出select
		case c := <-ch:
			fmt.Printf("%v ", c)
		case <-time.After(10 * time.Second):
			fmt.Println("timeout!")
		}
	}
}

func testChannel() {
	/*
		方向只有<-,表示数据从右向左传输,可以看作先进先出的队列
		由于channel自带阻塞特性,所以可以用来模拟WaitGroup,Mutex
		带有缓冲的channel,缓冲区满时插入数据会阻塞,缓冲区空时获取数据会阻塞
	*/
	// 信道当WaitGroup使用
	done := make(chan bool)
	go func() {
		for i := 0; i < 5; i++ {
			fmt.Printf("%v ", i)
		}
		done <- true
	}()
	<-done

	// 信道当锁使用
	wg := sync.WaitGroup{}
	chanLock := make(chan bool, 1)
	var x int
	for i := 0; i < 9999; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			chanLock <- true
			x++
			<-chanLock
		}()
	}
	wg.Wait()
	fmt.Printf("\n%v", x)
}

func testDefer() {
	value := 2

	defer func() { // 匿名函数定义
		err := recover() // 只有在相同的协程中调用recover才能处理错误,不处理错误会使主进程终止
		if err != nil {
			fmt.Printf("position 1, error: %v\n", err)
		}
	}()

	defer func(value int) { // defer在函数结束时被调用(return语句之后),当一个函数内多次调用defer时,按后进先出顺序执行
		fmt.Println("position 2,", value) // 输出2, 在执行defer语句时就会对延迟函数的实参进行求值
	}(value)

	value = 10
	panic("make mistakes")
	fmt.Println("不会再被执行")
}

func testMutex() {
	rwLock := sync.RWMutex{} // 读写锁,传递要使用指针
	rwLock.Lock()
	for i := 0; i < 4; i++ {
		go func(i int) {
			fmt.Printf("第 %d 个协程准备开始... \n", i)
			rwLock.RLock()
			fmt.Printf("第 %d 个协程获得读锁, sleep 1s 后，释放锁\n", i)
			time.Sleep(time.Second)
			rwLock.RUnlock()
		}(i)
	}
	time.Sleep(time.Second * 2)
	fmt.Println("准备释放写锁，读锁不再阻塞")
	rwLock.Unlock() // 写锁一释放,读锁就自由了
	time.Sleep(time.Second)
	rwLock.Lock() // 会等读锁全部释放,才能获得写锁
	fmt.Println("程序退出...")
	rwLock.Unlock()
}

func main() {
	//testWaitGroup()
	//testRaceCondition()
	//testSelect()
	//testChannel()
	testDefer()
	//testMutex()
}