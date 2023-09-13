package com.kugou.demo;

import com.kugou.model.Customer;
import com.kugou.util.Injection;
import com.kugou.util.Resilience;
import com.kugou.web.AppRunner;
import com.kugou.web.WebControl;
import com.kugou.web.WebMain;
import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.ApplicationContext;
import org.springframework.context.support.ClassPathXmlApplicationContext;


@SpringBootTest(classes={WebMain.class}) // tells Spring Boot to look for a main configuration class (one with @SpringBootApplication, for instance) and use that to start a Spring application context.
class ApplicationTests {

    @Autowired  // 应为WebControl被@Controller修饰,所以才可以被自动装载
    private WebControl webControl;
    @Autowired
    private Injection injection;

    private Resilience resilience = new Resilience();

    @Test
    @Disabled
    void contextLoads() {
        System.out.println("Injection: "+ injection);
        Customer customer = webControl.hello("aaa", "12");
        System.out.println("customer: "+customer);
    }

    @Test
    @Disabled
    void testBean(){
        // 启动工厂
        ApplicationContext context = new ClassPathXmlApplicationContext("classpath:spring.xml");
        // 获取组件
//        AppRunner runner = context.getBean("app_runner",AppRunner.class);
    }

    @Test
    void testResilience() throws Exception{
        resilience.testBreaker();
        resilience.testLimiter();
    }
}
