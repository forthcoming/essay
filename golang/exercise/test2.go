package main

import (
	"context"
	"fmt"
	"time"
)

var begin = time.Now()

func log(text string) {
	fmt.Println(time.Since(begin), "\t", text)
}

func mark(task string) func() {
	log(" ==> " + task + "...")
	return func() {
		log("<==  " + task + "...")
	}
}

// Tasks

func task1(ctx context.Context) {
	defer mark("task_1")()
	task2(ctx)
}

func task2(ctx context.Context) {
	defer mark("task_2")()
	//	Create a cancelable context
	ctx2, cancel := context.WithCancel(ctx)
	defer cancel()

	//	Call following tasks
	task3(ctx2)
}

func task3(ctx context.Context) {
	defer mark("task_3")()
	//	Create a context with 5 seconds timeout
	ctx3, cancel := context.WithTimeout(ctx, time.Second*5)
	defer cancel()

	//	Call following tasks
	go task4(ctx3)
	go task5(ctx3)

	//	wait until be canceled
	select {
	case <-ctx3.Done():
		log("task3: <- context.Done()")
	}
}

func task4(ctx context.Context) {
	defer mark("task_4")()
	//	Create a context with 3 seconds timeout
	ctx4, cancel := context.WithTimeout(ctx, time.Second*3)
	defer cancel()

	//	wait until be canceled
	select {
	case <-ctx4.Done():
		log("task4: <- context.Done()")
	}
}

func task5(ctx context.Context) {
	defer mark("task_5")()
	//	Create context with 5 seconds timeout
	ctx5, cancel := context.WithTimeout(ctx, time.Second*6)
	defer cancel()

	//	Call following tasks
	go task6(ctx5)

	//	wait until be canceled
	select {
	case <-ctx5.Done():
		log("task5: <- context.Done()")
	}
}

func task6(ctx context.Context) {
	defer mark("task_6")()
	//	Create a context with a value in it
	ctx6 := context.WithValue(ctx, "userID", 12)

	//	wait until be canceled
	select {
	case <-ctx6.Done():
		log("task6: <- context.Done()")
	}
}

func main() {
	task1(context.Background())
	/*
	       task1
	         | 顺序
	       task2
	         | 顺序
	       task3
	   协程 /   \ 协程
	    task4 task5
	            | 协程
	          task6
	*/
}
