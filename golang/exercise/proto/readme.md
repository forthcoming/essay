安装命令:  
sudo apt install golang-goprotobuf-dev    

执行命令:    
protoc -I=exercise/proto --go_out=exercise/proto tutorial.proto

生成一个tutorial.pb.go文件,每个消息类型对应一个结构体
