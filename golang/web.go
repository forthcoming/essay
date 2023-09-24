package main

import (
	"fmt"
	"github.com/gin-gonic/gin"
	"net/http"
	"time"
)

func MiddleWare() gin.HandlerFunc {
	return func(c *gin.Context) {
		t := time.Now()
		fmt.Println("中间件开始执行了")
		c.Set("request", "中间件") // 设置变量到Context的key中,可以通过Get()取
		c.Next()                   // c.Next前面是请求前逻辑,后面是请求后逻辑
		status := c.Writer.Status()
		fmt.Println("中间件执行完毕", status)
		latency := time.Since(t)
		fmt.Println("time:", latency)
	}
}

func main() {
	// 创建路由,基于Radix树的路由,小内存占用
	r := gin.Default()  // 默认注册gin.Logger()和gin.Recovery()中间件,Recovery会recover任何panic
	r.Use(MiddleWare()) // 注册自定义全局中间件,如果有多个中间件,请求前按顺序执行,请求后按逆序执行

	r.GET("/ping", func(c *gin.Context) { // 绑定路由规则,执行函数,gin.Context封装了request和response
		//  /ping/:name?firstname=Jane&lastname=Doe
		_ = c.DefaultQuery("firstname", "Guest")
		_ = c.Query("lastname") // URL参数
		_ = c.Param("name")     // API参数
		_, _ = c.Get("request") // 中间件 true

		cookie, err := c.Cookie("gin_cookie")
		if err != nil {
			cookie = "NotSet"
			c.SetCookie("gin_cookie", "test", 3600, "/", "localhost", false, true)
		}
		fmt.Printf("Cookie value: %s \n", cookie)

		c.String(http.StatusOK, "hello World!")
	})

	r.POST("/foo", func(c *gin.Context) { // 可以针对具体的请求自定义局部中间件,执行顺序参考r.Use()
		c.JSON(http.StatusOK, "foo")
		_ = c.PostForm("username") // 表单参数,传输为post请求,PostForm默认解析的是x-www-form-urlencoded或from-data格式的参数
	})

	s := &http.Server{
		Addr:           ":8080", // 监听端口,默认为8080
		Handler:        r,
		ReadTimeout:    10 * time.Second,
		WriteTimeout:   10 * time.Second,
		MaxHeaderBytes: 1 << 20,
	}
	s.ListenAndServe()
	// 也可以通过r.Run(":8000")直接运行
}
