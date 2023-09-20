package main

import (
	"github.com/gin-gonic/gin"
	"net/http"
)

func main() {
	r := gin.Default()                // 创建路由
	r.GET("/", func(c *gin.Context) { // 绑定路由规则，执行的函数,gin.Context，封装了request和response
		c.String(http.StatusOK, "hello World!")
	})
	r.Run(":8000") // 监听端口,默认为8080
}
