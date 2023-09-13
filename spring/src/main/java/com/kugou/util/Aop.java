package com.kugou.util;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.Signature;
import org.aspectj.lang.annotation.*;
import org.aspectj.lang.reflect.MethodSignature;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;

import javax.servlet.http.HttpServletRequest;
import java.lang.reflect.Method;


// 本配置类只能放在Springboot启动入口所在目录下才会被装载
@Component
@Aspect
@Order(2)
public class Aop {

    @Pointcut("execution(public * com.kugou.web.WebControl.say(..))")  // ..意思是不管参数有多少个,只要函数名匹配就行
    public void sayLogPointcut(){}

    @Pointcut("execution(public * com.kugou.web.WebControl.*(..))")   // 匹配WebControl下的所有函数
    public void logPointcut(){}

    @Before("sayLogPointcut()")
    public void writeSayLog(){
        System.out.println("in Aop before writing say api log...");
    }

    @After("logPointcut()")
    public void writeLog(){
        System.out.println("in Aop after writing all api log...");
    }

    @AfterReturning(pointcut = "logPointcut()",returning = "obj")
    public void getApiReturning(Object obj){
        System.out.println("in Aop after the api return "+obj);  // obj是函数返回值
    }

    // @Around("logPointcut()")  // 可以取代@Before和@After,@AfterReturning.但必须要调用proceed方法
    @Around("@annotation(org.springframework.web.bind.annotation.GetMapping) || @annotation(org.springframework.web.bind.annotation.RequestMapping)")
    public Object doAround(ProceedingJoinPoint pjp) throws Throwable {
        System.out.println("in Aop do around work...");

        Object[] args = pjp.getArgs();
        Object ret = pjp.proceed(args);

        Signature signature = pjp.getSignature();
        String methodName = signature.getName();
        Method method = ((MethodSignature) signature).getMethod();

//        Class<?>[] parameterTypes = ((MethodSignature) signature).getMethod().getParameterTypes();
//        Object target = pjp.getTarget();
//        Method methodV1 = target.getClass().getMethod(methodName, parameterTypes);

        if (method.isAnnotationPresent(GetMapping.class)||method.isAnnotationPresent(RequestMapping.class)){
            HttpServletRequest request=null;
            for(Object arg:args) {
                if(arg instanceof HttpServletRequest) {
                    request = (HttpServletRequest)arg;
                    System.out.println(request.getHeader("user-agent"));
                }
            }
        }

        System.out.println(String.format("in Aop do around work over, function name is %s:%s",signature.getDeclaringTypeName(),methodName));
        return ret;
    }
}


@Component
@Aspect
@Order(1)  // 相同切入点数字越小优先级越高
class AnotherAop {

    @Before("execution(public * com.kugou.web.WebControl.say(..))")
    public void writeSayLog(){
        System.out.println("in AnotherAop before writing say api log...");
    }

}
