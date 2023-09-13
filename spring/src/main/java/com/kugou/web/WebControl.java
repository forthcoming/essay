package com.kugou.web;

import com.ctrip.framework.apollo.Config;
import com.ctrip.framework.apollo.spring.annotation.ApolloConfig;
import com.kugou.model.Customer;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import com.kugou.util.TestComponent;

@Controller  // 表示类会以url形式对外服务
@RequestMapping(path = "web")
public class WebControl {

    @Resource
    private AppRunner runner;

    @ApolloConfig   // 默认application
    private Config appConfig;

    @ApolloConfig("KTV.chat_service")
    private Config chatConfig;

    @Autowired
    private TestComponent component;

    @Autowired
    private TestComponent componentAnother;

    @RequestMapping(path = "say", method = {RequestMethod.GET, RequestMethod.POST})
    public String say(HttpServletRequest request, Model model, HttpServletResponse resp) {
        System.out.println(appConfig.getProperty("keys","default_value"));
        System.out.println(request.getHeader("user-agent"));
        System.out.println(request.getQueryString());   // 获取requests.get或者requests.post的params数据
        System.out.println(request.getParameter("name"));  // 获取requests.post提交的data数据(非json数据)
        model.addAttribute("color","red");
        resp.setHeader("source","spring");  // 设置响应头
        return "saying"; // Thymeleaf parses the saying.html template and evaluates the th:text expression to render the value of the ${color} parameter that was set in the controller.
    }

    @ResponseBody  // @RestController combines @Controller and @ResponseBody, two annotations that results in web requests returning data rather than a view.
    @GetMapping("/hello")
    public Customer hello(@RequestParam(value = "name", required = false,defaultValue = "World") String name, @RequestParam(value = "id", defaultValue = "12") String _id) {
        runner.run();
        return new Customer(Integer.parseInt(_id),name,"Lucas","root");  // 展示Customer实现了getter方法的字段
    }

}


