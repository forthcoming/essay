package web

import (
	"bytes"
	"github.com/gin-gonic/gin"
	"net/textproto"
	"strings"
)

var (
	defaultAllowHeaders = []string{
		"Keep-Alive",
		"User-Agent",
		"Content-Type",
		"Authorization",
		"X-Cf-Device-Id",
		"X-Cf-Platform",
		"X-Cf-Uid",
		"X-Cf-Appid",
		"X-Cf-Gray-Key",
		"X-Cf-Svc-Canary-Key", // 这个可有可无，客户端不会请求这个Header
	}
	defaultAllowHeadersMap    = make(map[string]bool)
	defaultAllowHeadersString = strings.Join(defaultAllowHeaders, ",")
)

func init() {
	for _, h := range defaultAllowHeaders {
		h = textproto.CanonicalMIMEHeaderKey(h)
		defaultAllowHeadersMap[h] = true
	}
}

// 根据客户端请求的 Access-Control-Request-Headers 来确定最终的 Access-Control-Allow-Headers
func getAllowHeaders(c *gin.Context) string {
	reqHeaders := c.Request.Header.Get("Access-Control-Request-Headers")
	if reqHeaders == "" {
		return defaultAllowHeadersString
	}

	res := bytes.NewBuffer(make([]byte, 0, len(defaultAllowHeadersString)+len(reqHeaders)+1))
	res.WriteString(defaultAllowHeadersString)
	for _, h := range strings.Split(reqHeaders, ",") {
		h = textproto.CanonicalMIMEHeaderKey(strings.TrimSpace(h))
		if defaultAllowHeadersMap[h] {
			continue
		}
		if !strings.HasPrefix(h, "X-Cf-") {
			continue
		}
		res.WriteByte(',')
		res.WriteString(h)
	}
	return res.String()
}

// Cors 自定义跨域中间件
// 跨域资源共享(CORS)是一种机制,它使用额外的HTTP头来告诉浏览器,让运行在一个origin(domain)上的Web应用被准许访问来自不同源服务器上的指定的资源
// 当一个资源从与该资源本身所在的服务器不同的域、协议或端口请求一个资源时,资源会发起一个跨域HTTP请求
// 浏览器先往目标url发起options请求,根据服务端返回的Allow-Origin等信息判断是否继续进行跨域请求
// Ref: https://github.com/gin-contrib/cors
// Ref: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Headers/Access-Control-Allow-Headers
// Ref: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Access_control_CORS
func Cors() gin.HandlerFunc {
	return func(c *gin.Context) {
		header := c.Writer.Header()
		header.Set("Access-Control-Allow-Origin", "*")
		header.Set("Access-Control-Allow-Credentials", "true")
		header.Set("Access-Control-Allow-Methods", "GET, POST")
		header.Set("Access-Control-Max-Age", "600")
		header.Set("Access-Control-Allow-Headers", getAllowHeaders(c))
		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}
		if c.Request.Method == "HEAD" {
			c.AbortWithStatus(200)
			return
		}
	}
}
