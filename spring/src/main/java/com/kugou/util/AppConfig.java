package com.kugou.util;

import com.kugou.dao.BookRepository;
import com.kugou.web.AppRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Lazy;
import org.springframework.context.annotation.Scope;

import java.util.HashMap;
import java.util.List;


// 本配置类只能放在Springboot启动入口所在目录下才会被装载
@Configuration  // The AppConfig class above would be equivalent to the following Spring <beans/> XML
public class AppConfig {

    @Scope("singleton")  // 默认为单例模式,跟xml中保持一致
    @Lazy  // 单例模式下会随着工厂的启动而创建一次,@Lazy意思是只在第一次使用的时候(@Autowired)创建一次
    @Bean(name = "init_injection")  // name用于指定bean的id,如果不指定,则函数名作为bean的id
    public Injection initInjection(){
        /*
          <bean id="init_injection" class="com.kugou.util.Injection">
              <constructor-arg index="0" value="69"/>
              <property name="id" value="6"/>
              <property name="name" value="avatar"/>
              <property name="gender" value="true"/>
              <property name="list">
                  <list>
                      <value>hello</value>
                      <value>2</value>
                  </list>
              </property>
              <property name="map">
                  <map>
                      <entry key="password" value="pwd"/>
                  </map>
              </property>
          </bean>
        * */
        Injection injection = new Injection(69);
        injection.setId(6);
        injection.setName("avatar");
        injection.setGender(true);
        injection.setList(List.of("hello",2));
        HashMap<String,Object> hashMap = new HashMap<>();
        hashMap.put("password",2);
        injection.setMap(hashMap);
        return injection;
    }

    @Bean
    public AsyncService async_service(){
        // <bean id="async_service" class="com.kugou.util.AsyncService" />
        return new AsyncService();
    }

    @Bean
    public AsyncService async_service_v1(){
        // <bean id="async_service_v1" class="com.kugou.util.AsyncService" />
        return new AsyncService();
    }

    @Bean
    public AsyncServiceSon async_service_son(){
        // <bean id="async_service_son" class="com.kugou.util.AsyncServiceSon" />
        return new AsyncServiceSon();
    }

    @Bean
    public String asyncService(){   // 测试byName
        // <bean id="asyncService" class="java.lang.String" />
        return "";
    }

    @Scope("prototype")
    @Bean(name = "app_runner")
    public AppRunner initAppRunner(BookRepository bookRepository){  // 实现的bean可以放在下面
        /*
        <bean id="app_runner" class="com.kugou.web.AppRunner" scope="prototype">
            <!--  sprig启动时读取该配置文件,创建对应的类对象,并用唯一id作标识 -->
            <!--  调用com.kugou.web.AppRunner.setBookRepository方法,用id=book_repository实例初始化bookRepository变量  -->
            <!--  scope默认是singleton,一个Bean容器只存在一份,随着工厂的启动创建,prototype意思是每次使用创建新的实例,使用时才会创建 -->
            <property name="bookRepository" ref="book_repository"/>
        </bean>
        * */
        AppRunner runner = new AppRunner();
        runner.setBookRepository(bookRepository);
        return runner;
    }

    @Bean(name = "book_repository")
    public BookRepository initBookRepository(){
        // <bean id="book_repository" class="com.kugou.dao.BookRepository"/>
        return new BookRepository();
    }
}
