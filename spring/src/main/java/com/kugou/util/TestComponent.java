package com.kugou.util;


import org.springframework.context.annotation.Scope;
import org.springframework.stereotype.Component;


@Component  // Spring会把Component注解的类加到javaBean,默认是单例模式
@Scope("prototype")  // 多例模式
public class TestComponent {

    public TestComponent(){
        System.out.println(String.format("init TestComponent,id is %s",this));
    }

}
