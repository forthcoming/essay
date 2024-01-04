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
// Ref: https://github.com/gin-contrib/cors
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
