package inner_package

import (
	"fmt"
	_ "sync" // 导入一个未使用的包会导致编译错误, 但有时候我们只想导入包: 它会计算包级变量的初始化表达式和执行导入包的init初始化函数
	"time"
)

func main() {
	//c := make(chan int) //声明一个int类型的无缓冲通道
	//c <- 1  // 由于channel这种阻塞发送方和接收方的特性，如果我们在一个线程内向同一个channel同时进行读取和发送的操作，就会导致死锁。
	//i := <- c
	//fmt.Printf("receive %d\n", i)


	//go spinner(100 * time.Millisecond)
	//const n = 45
	//fibN := fib(n) // slow
	//fmt.Printf("\rFibonacci(%d) = %d\n", n, fibN)

	c := make(chan int)		//声明一个int类型的无缓冲通道
	go func() {
		fmt.Println("ready to send in g1")
		c <- 1
		fmt.Println("send 1 to chan")
		fmt.Println("goroutine start sleep 1 second")
		time.Sleep(time.Second)
		fmt.Println("goroutine end sleep")
		c <- 2
		fmt.Println("send 2 to chan")
	}()

	//fmt.Println("main thread start sleep 1 second")
	//time.Sleep(time.Second)
	//fmt.Println("main thread end sleep")
	//i,ok := <- c
	//fmt.Printf("receive %d, ok %t\n", i,ok)
	//i = <- c
	//fmt.Printf("receive %d\n", i)
	//time.Sleep(time.Second)
	//close(c)
	//关闭channel的操作原则上应该由发送者完成，因为如果仍然向一个已关闭的channel发送数据，会导致程序抛出panic
	//从一个已关闭的channel中读取数据不会报错。只不过需要注意的是，接受者就不会被一个已关闭的channel的阻塞。
	//而且接受者从关闭的channel中仍然可以读取出数据，只不过是这个channel的数据类型的默认值

}

func spinner(delay time.Duration) {
	for {
		for _, r := range `-\|/` {
			fmt.Printf("\r%c", r)
			time.Sleep(delay)
		}
	}
}

func fib(x int) int {
	if x < 2 {
		return x
	}
	return fib(x-1) + fib(x-2)
}