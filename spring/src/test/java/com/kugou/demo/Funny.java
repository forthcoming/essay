package com.kugou.demo;

import org.junit.jupiter.api.*;
import org.junit.jupiter.api.Test;
import com.google.common.collect.*;

//同一个包下面的文件都需要此声明，同一个包中的类名字是不同的，不同的包中的类的名字是可以相同的
//当同时调用两个不同包中相同类名的类时，应该加上包名加以区别
//包声明应该在源文件的第一行，每个源文件只能有一个包声明，这个文件中的每个类型都应用于它。
//如果一个源文件中没有使用包声明，那么其中的类，函数，枚举，注释等将被放在一个无名的包（unnamed package）中。
//类目录的绝对路径叫做 class path。设置在系统变量 CLASSPATH 中。编译器和 java 虚拟机通过将 package 名字加到 class path 后来构造 .class 文件的路径。

@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
@DisplayName("A special test case")
public class Funny {
    // 类似的还有@BeforeAll和@AfterAll,但他们只会执行一次
    @BeforeEach
    public void init(){
        System.out.println("in init");
        // 所有测试方法执行前都会先执行该方法
    }

    @AfterEach
    public void destroy(){
        // 所有测试方法执行后都会执行该方法(即使测试方法失败也会执行destroy方法)
    }

    @Order(2)  // 使用前提是类被@TestMethodOrder说明
//    @Disabled   // 不测试该函数
    @RepeatedTest(3)
    public void testAdd() {
        int a = 12;
        System.out.println("testAdd");
        Assertions.assertEquals(12,a);
    }

    @Order(1)
    @Timeout(3)
    @DisplayName("\uD83D\uDE31")  // 更改展示的名字
    @Test
    public void testMinus() throws Exception {
        int a = 5;
        System.out.println("testMinus");
        Assertions.assertEquals(a,5);
        Thread.sleep(2000);  // 单位毫秒
    }

}
