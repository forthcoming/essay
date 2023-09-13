package com.kugou.dao;

import com.kugou.model.Book;
import org.springframework.cache.annotation.Cacheable;


public class BookRepository {

    // 使用前提是主入口声明了@EnableCaching
    @Cacheable(value = "books",key = "#isbn")  // key说明用哪些参数决定是否使用缓存,Default is "" meaning all method parameters are considered as a key
    public Book getByIsbn(String isbn,int index) {
        try {
            long time = 3000L;
            Thread.sleep(3000);
        } catch (InterruptedException e) {
            throw new IllegalStateException(e);
        }
        return new Book(isbn, "Some book");
    }

}