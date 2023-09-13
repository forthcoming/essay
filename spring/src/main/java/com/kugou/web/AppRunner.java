package com.kugou.web;

import com.kugou.dao.BookRepository;
import com.kugou.util.AsyncService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.CommandLineRunner;

import javax.annotation.Resource;
import java.util.Arrays;
import java.util.HashSet;
import java.util.concurrent.CompletableFuture;

public class AppRunner implements CommandLineRunner {  // spring启动时会执行本类的run方法

    private static final Logger logger = LoggerFactory.getLogger(AppRunner.class);

//    @Qualifier("async_service")   // 指定用哪个id来完成装载,当工厂中出现多个同类型实例或子类实例,则需要手动指定
//    @Autowired(required = false)    // 自动被id=async_service的bean装载,required意思是bean是否可以不存在
    @Resource(name = "async_service")  // 按id装载,相当于@Qualifier+@Autowired,如果未指定name,会先匹配id=asyncService的bean(byName),没找到则继续匹配类型是AsyncService的bean(byType)
    private AsyncService asyncService;

    private BookRepository bookRepository;   // 装载AppRunner时会调用setBookRepository对其进行装载

    public void setBookRepository(BookRepository bookRepository) {
        this.bookRepository = bookRepository;
    }

    @Override
    public void run(String... args) {
        logger.info(".... Fetching books");
        logger.info("isbn-1234 -->" + bookRepository.getByIsbn("isbn-1234",1));
        logger.info("isbn-4567 -->" + bookRepository.getByIsbn("isbn-4567",2));
        logger.info("isbn-1234 -->" + bookRepository.getByIsbn("isbn-1234",3));
        logger.info("isbn-4567 -->" + bookRepository.getByIsbn("isbn-4567",4));
        logger.info("isbn-1234 -->" + bookRepository.getByIsbn("isbn-1234",5));
        logger.info("isbn-1234 -->" + bookRepository.getByIsbn("isbn-1234",6));

        try{
            long start = System.currentTimeMillis();  // Start the clock
            // Kick of multiple, asynchronous tasks
            CompletableFuture<HashSet<?>> result1 = asyncService.task("PivotalSoftware",1);
            CompletableFuture<HashSet<?>> result2 = asyncService.task("CloudFoundry",2);
            CompletableFuture<HashSet<?>> result3 = asyncService.task("Spring-Projects",3);

            CompletableFuture.allOf(result1,result2,result3).join();  // Wait until they are all done

            logger.info("Elapsed time: " + (System.currentTimeMillis() - start));
            logger.info("--> " + result1.get());
            logger.info("--> " + result2.get());
            logger.info("--> " + result3.get());
        } catch (Exception e){
            System.out.println("error found: "+ Arrays.toString(e.getStackTrace()));
        }

    }

}
