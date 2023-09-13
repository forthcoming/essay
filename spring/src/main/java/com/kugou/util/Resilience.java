package com.kugou.util;

import io.github.resilience4j.circuitbreaker.CircuitBreaker;
import io.github.resilience4j.circuitbreaker.CircuitBreakerConfig;
import io.github.resilience4j.circuitbreaker.CircuitBreakerRegistry;
import io.github.resilience4j.decorators.Decorators;
import io.github.resilience4j.ratelimiter.RateLimiter;
import io.github.resilience4j.ratelimiter.RateLimiterConfig;
import io.github.resilience4j.retry.Retry;
import io.vavr.control.Try;

import java.io.IOException;
import java.time.Duration;
import java.util.concurrent.TimeoutException;
import java.util.function.Supplier;


public class Resilience {

    public void testBreaker(){
        // Create a custom configuration for a CircuitBreaker
        CircuitBreakerConfig circuitBreakerConfig = CircuitBreakerConfig.custom()
                .failureRateThreshold(50)  // When the failure rate is equal or greater than the threshold the CircuitBreaker transitions to open and starts short-circuiting calls.
                .slowCallRateThreshold(100) // The CircuitBreaker considers a call as slow when the call duration is greater than slowCallDurationThreshold
                .slowCallDurationThreshold(Duration.ofMillis(60000))
                .waitDurationInOpenState(Duration.ofMillis(1000))  // The time that the CircuitBreaker should wait before transitioning from open to half-open.
                .permittedNumberOfCallsInHalfOpenState(2) // Configures the number of permitted calls when the CircuitBreaker is half open.
                .recordExceptions(IOException.class, TimeoutException.class)
                .ignoreExceptions(RuntimeException.class)
                .build();
        /*
        recordExceptions:
        A list of exceptions that are recorded as a failure and thus increase the failure rate.
        Any exception matching or inheriting from one of the list counts as a failure, unless explicitly ignored via ignoreExceptions.
        If you specify a list of exceptions, all other exceptions count as a success, unless they are explicitly ignored by ignoreExceptions.

        ignoreExceptions:
        A list of exceptions that are ignored and neither count as a failure nor success.
        Any exception matching or inheriting from one of the list will not count as a failure nor success, even if the exceptions is part of recordExceptions.
        * */

        // Create a CircuitBreakerRegistry with a custom global configuration
        CircuitBreakerRegistry circuitBreakerRegistry = CircuitBreakerRegistry.of(circuitBreakerConfig);
        CircuitBreaker circuitBreaker = circuitBreakerRegistry.circuitBreaker("config_breaker");
        // Create a Retry with default configuration,3 retry attempts and a fixed time interval between retries of 500ms
        Retry retry = Retry.ofDefaults("config_retry");
        // Decorate your call to Resilience.doSomething() with a CircuitBreaker and Retry
        Supplier<Object> decoratedSupplier = Decorators.ofSupplier(Resilience::doSomething)
                .withCircuitBreaker(circuitBreaker)
                .withRetry(retry)
                .decorate();
        // Execute the decorated supplier and recover from any exception
        Object result = Try.ofSupplier(decoratedSupplier).recover(throwable -> "Hello from Recovery").get(); // 执行Resilience::doSomething
        System.out.println("result is "+result);


        // Create a CircuitBreaker with default configuration
        CircuitBreaker breaker = CircuitBreaker.ofDefaults("default_breaker");
        Supplier<Object> breakerSupplier = CircuitBreaker.decorateSupplier(breaker, Resilience::doSomething);
        // When you don't want to decorate your lambda expression,but just execute it and protect the call by a CircuitBreaker.
        Object output = Try.ofSupplier(breakerSupplier).recover(throwable -> "Hello from Recovery").get();
        System.out.println("simple result is "+output);
    }

    public void testLimiter() throws InterruptedException {
        // Create a custom RateLimiter configuration
        RateLimiterConfig config = RateLimiterConfig.custom()
                .timeoutDuration(Duration.ofMillis(100))  // The default wait time a thread waits for a permission
                .limitRefreshPeriod(Duration.ofSeconds(1)) // The period of a limit refresh. After each period the rate limiter sets its permissions count back to the limitForPeriod value
                .limitForPeriod(1)  // The number of permissions available during one limit refresh period
                .build();
        RateLimiter rateLimiter = RateLimiter.of("config_limiter", config);
        // Decorate your call to Resilience.testLimiter()
        Supplier<?> restrictedSupplier = RateLimiter.decorateSupplier(rateLimiter, Resilience::doAnything);
        // First call is successful
        Try<?> firstTry = Try.ofSupplier(restrictedSupplier);
        System.out.println(firstTry.isSuccess());
        // Second call fails, because the call was not permitted
//        Thread.sleep(1500);
        Try<?> secondTry = Try.ofSupplier(restrictedSupplier);
        System.out.println(secondTry.isSuccess());
        if(secondTry.isFailure()){
            System.out.println(secondTry.getCause());
        }
    }

    static Object doSomething(){
        System.out.println("do something");
        return 1/0;
    }

    static boolean doAnything(){
        System.out.println("do anything");
        return true;
    }
}
