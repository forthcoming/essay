package com.kugou.util;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.util.HashSet;
import java.util.concurrent.CompletableFuture;

@Service  // making it a candidate for Spring’s component scanning to detect and add to the application context
public class AsyncService {

    private static final Logger logger = LoggerFactory.getLogger(AsyncService.class);

    @Async  // indicating that it should run on a separate thread.
    public CompletableFuture<HashSet<?>> task(String user, Integer age) throws InterruptedException {
        logger.info("Looking up " + user);
        Thread.sleep(1000L);     // Artificial delay of 1s for demonstration purposes
        HashSet<Object> hashSet = new HashSet<>();
        hashSet.add(user);
        hashSet.add(age);
        return CompletableFuture.completedFuture(hashSet);
    }

}

