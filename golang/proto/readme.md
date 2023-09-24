安装命令:  
https://github.com/protocolbuffers/protobuf/releases/tag/v24.3 下载二进制包  

执行命令:    
protoc -I=proto --go_out=proto tutorial.proto  # 在proto同级目录执行,生成一个tutorial.pb.go文件,每个消息类型对应一个结构体
