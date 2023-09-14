package main

import (
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

// 主协程退出,其他子协程也要跟着退出,Goroutine没有ID号

func f1(ch1 chan<- int, wg *sync.WaitGroup) {
	defer wg.Done()
	for i := 0; i < 10; i++ {
		ch1 <- i
	}
	close(ch1) // 用完关闭,防止f2死锁,通道关闭后可以取到默认值,且第二个参数是false
}

func f2(ch1 <-chan int, ch2 chan<- int, wg *sync.WaitGroup) { // 单向通道,限定通道方向
	defer wg.Done()
	for i := range ch1 {
		ch2 <- i * i
	}
	close(ch2)
}

var counter = 0

func TestRaceCondition(lock *sync.Mutex, wg *sync.WaitGroup) {
	lock.Lock()
	defer lock.Unlock()
	defer wg.Done() // 等价于wg.Add(-1)
	counter++
}

func main() {
	wg := sync.WaitGroup{}   // WaitGroup传递要使用指针
	lock := sync.Mutex{}     // 互斥锁,传递要使用指针
	rwLock := sync.RWMutex{} // 读写锁,传递要使用指针

	mapping := sync.Map{} // 该map并发安全,读写通过Load和Store实现,key-value类型可以不同
	mapping.Store("key", "value")
	mapping.Store(1, 'A')

	ch1 := make(chan int, 5)  // make返回的都是引用类型
	ch2 := make(chan int, 10) // 定义channel的时候也可以定义单向通道,双向通道可以作为单向通道的入参
	wg.Add(2)
	go f1(ch1, &wg)
	go f2(ch1, ch2, &wg)
	wg.Wait()
	for ret := range ch2 {
		fmt.Println(ret)
	}

	for i := 0; i < 50000; i++ {
		wg.Add(1) // 一定要在Wait函数执行前执行
		go TestRaceCondition(&lock, &wg)
	}
	wg.Wait() // 会阻塞代码的运行,直到计数器值减为0
	fmt.Println("counter的值是 ", counter)

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

	// 信道当WaitGroup使用
	done := make(chan bool)
	go func() {
		for i := 0; i < 5; i++ {
			fmt.Println(i)
		}
		done <- true
	}()
	<-done

	// 信道当锁使用
	chanLock := make(chan bool, 1)
	var x int
	for i := 0; i < 1000; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			chanLock <- true
			x++
			<-chanLock
		}()
	}
	wg.Wait()
	fmt.Println(x)

	var total int32 = 0
	for i := 0; i < 1000; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			atomic.AddInt32(&total, 2) // 效率比锁更高
		}()
	}
	wg.Wait()
	fmt.Println(total)

	channel := make(chan int, 5) // 如果缓冲区大于1,可以看到输出结果不唯一,说明select是随机选取一个case执行
	for i := 0; i < 10; i++ {
		select {
		case x := <-channel:
			fmt.Println(x)
		case channel <- i:
		}
	}

	ch := make(chan int)
	stop := make(chan bool)
	go func() {
		for j := 0; j < 7; j++ {
			ch <- j
			time.Sleep(time.Second)
		}
		//close(ch)  // 注意这里不要close,应为close一个channel也可以使select语句不再阻塞,for中的channel要close
		time.Sleep(time.Second)
		stop <- true
	}()
	for { // 死循环
		select {
		case c := <-ch:
			fmt.Println("Receive", c)
		case _ = <-stop:
			goto ENDLOOP // 此处不能用break,应为break仅仅退出select
		case <-time.After(10 * time.Second):
			fmt.Println("timeout!")
		}
	}
ENDLOOP:
}

func sendRegisterEmailAsync(destination, here string) {
	// 通过go biz.sendRegisterEmailAsync(ctx, email, "cloud.tencent.com")方式调用
	// 调用的时候不需要sync.WaitGroup等待协成结束,应为程序一直在运行
	defer func() { // Use this deferred function to handle errors.
		err := recover() // 只有在相同的Go协程中调用recover才管用,recover不能恢复一个不同协程的panic
		if err != nil {
			fmt.Printf("in sendRegisterEmailAsync err=%v\n", err)
		}
	}() // 必须, 否则协程报错会使主进程终止
	//data := map[string]interface{}{
	//	"here":  here,
	//	"email": destination,
	//}
	//_ = biz.EmailClient.SendEmail(ctx, destination, "Register", data)
}
