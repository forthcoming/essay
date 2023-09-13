package com.kugou.util;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.text.SimpleDateFormat;
import java.util.Date;

@Component
public class ScheduledTasks {

    private static final Logger log = LoggerFactory.getLogger(ScheduledTasks.class);
    private static final SimpleDateFormat dateFormat = new SimpleDateFormat("HH:mm:ss");

    // @EnableScheduling,@Component,@Scheduled缺一不可
    // cron: A cron-like expression on the second, minute, hour, day of month, month, and day of week.For example, "0 * * * * MON-FRI" means once per minute on weekdays
    // fixedDelay: Execute the annotated method with a fixed period in milliseconds between the end of the last invocation and the start of the next.
    // fixedRate: Execute the annotated method with a fixed period in milliseconds between invocations.
    @Scheduled(fixedDelay = 30000)
    public void reportCurrentTime() throws Exception{
        Thread.sleep(1000);  // 验证fixedDelay和fixedRate区别
        log.info("The time is now {}", dateFormat.format(new Date()));
    }
}