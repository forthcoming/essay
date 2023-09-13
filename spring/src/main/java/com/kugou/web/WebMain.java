package com.kugou.web;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.ComponentScans;
import org.springframework.context.annotation.ImportResource;
import org.springframework.context.annotation.PropertySource;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.annotation.EnableScheduling;


@ComponentScans({@ComponentScan("com.kugou")})  // 指定需要扫描的包,不要直接使用ComponentScan,否则默认的ComponentScan会失效
@SpringBootApplication  // 包含ComponentScan注解,默认会扫描同包及子包下带有Component注解的组件
@EnableScheduling  // ensures that a background task executor is created. Without it, nothing gets scheduled.
@EnableCaching
@EnableAsync       // switches on Spring’s ability to run @Async methods in a background thread pool.
@ImportResource(locations = "classpath:spring.xml")
//@PropertySource("classpath:application.properties")
public class WebMain {

    public static void main(String[] args) {
        SpringApplication.run(WebMain.class, args);
//        SpringApplication.run(WebMain.class, args).close();
    }

}
