### common

```
Dockerfile 用来构建镜像，docker pull 用来下载镜像
容器是根据镜像创建的运行实例,可以是 created、running、exited、paused 等状态
同一个镜像可以创建多个相互独立的容器

容器内访问外部服务用的ip是宿主机ip
docker建议每个容器只运行一个服务
每个虚拟机都是独立的环境,容器共享操作系统,占用资源更少
mac系统docker desktop在engine设置页面新增:
"registry-mirrors": ["https://yxzrazem.mirror.aliyuncs.com","http://hub-mirror.c.163.com"]
sudo systemctl restart docker
sudo dockerd # 启动dockerd服务
```

### docker命令

```shell
docker info # 查看 Docker 客户端、服务端、存储驱动、容器、镜像、插件等系统级信息
docker system df # 查看镜像,容器,数据卷占用空间
docker pull image_name[:tag] # 拉镜像,如果不指定tag,默认值是latest
docker images [-a|--no-trunc]  # 查看本地镜像列表,-a显示所有镜像(默认隐藏中间镜像),--no-trunc意思是不要截断输出
docker rmi [-f] image_id|image_name[:tag] # 删除镜像,如果镜像对应的容器正在运行则无法删除,需-f强制删除
docker search [--no-trunc] nginx  # 搜索docker hub中的镜像
docker commit [-a 'author'|-m 'the first image'] container_id image_name[:tag] # 保存已经更改的容器为新镜像
docker login # 登录,不带服务器地址时,默认登录 Docker Hub
docker push yourname/image_name[:tag] # 推送本地镜像到远程仓库,需提前用docker login账户创建好仓库
docker tag old_image_name[:tag] yourname/image_name[:tag] # 给原镜像打标签,不复制镜像数据,指向同一个image_id
docker build -t image_name[:tag] [-f dir/Dockerfile] .  # 构建镜像,不指定-f则默认为当前目录下名为Dockerfile的文件,最后的 . 是构建上下文目录,Dockerfile 中的 COPY 和 ADD 只能访问构建上下文里的文件
docker history [--no-trunc] image_name[:tag] # 逆序查看镜像构建语句
docker save -o my-image.tar IMAGE[:TAG] # 保存镜像
docker load -i my-image.tar # 加载镜像

docker network ls   # 列出 Docker 网络
docker network inspect bridge_name   # 查看网络详情(包含哪些容器使用当前网络)
docker network create network_name  # 默认创建的是桥接网络

# 容器查看与管理命令
docker ps [-a] # 查看正在运行的容器(也可以查看容器的映射端口),-a查看所有容器
docker top [container_name|container_id]  # 查看容器中正在运行的进程
docker rm [-f] container_name|container_id  # 删除已经停止的容器,-f强制删除容器
docker start container_name|container_id # 启动已经停止的容器
docker restart container_name|container_id # 重新启动容器；运行中的容器会先停止再启动
docker stop container_name|container_id # 尝试优雅停止运行中的容器，超时后强制终止
docker attach container_name|container_id  # 将本地终端连接到容器主进程的标准输入输出；不会创建新的 Shell
docker exec container_name|container_id cmd  # 在运行中的容器中启动新进程,在容器环境执行命令,如docker exec -it redis /bin/bash
docker kill container_name|container_id # 默认发送 SIGKILL，立即强制终止容器；可通过 --signal 指定其他信号
docker logs [-tf] container_name|container_id # 查看容器控制台输出日志,-f参考linux的tail,-t显示时间戳
docker inspect image_id|container_id  # 查看镜像或容器的详细信息,只有启动的容器才分配IP,IP保存在IPAddress字段
docker inspect NETWORK|VOLUME # 查看网络、volume 等多种 Docker 对象
docker cp container_name|container_id:container_path local_path # 复制容器中的文件到宿主机,也支持从宿主机复制到容器
ctrl+p & ctrl+q # 退出容器
exit # 退出容器并停止容器

docker run image_id  # 运行本地镜像,如果镜像不存在,会先去dockerhub拉取镜像
--name: 指定容器名称
-d: 后台运行容器并打印容器id
-i: 以交互模式运行容器(通常与-t同时使用,此时Dockerfile中的CMD命令会被忽略)
-t: 为容器分配一个终端
-p: 宿主机:容器端口映射,可通过宿主机ip:port访问容器指定port程序
-v: 宿主机:容器目录映射,目录不存在会创建,存在则覆盖,改动本机或容器,则另一端目录内容也会改变
--rm: 容器退出时自动删除
-m: 以bytes为单位容器最大内存
-w: 容器工作目录,即进入时的目录,相当于执行cd操作,一般设置为安装软件目录,他会覆盖dockerfile中的WORKDIR
--network: 使用自定义网桥,容器之间可通过容器名互通,默认的bridge只能通过ip互通,互通前提是位于同一个网络,不同网桥间不互通
docker run -p 80:80 -v /usr/local/data:/container/data --name=test centos echo 'Hello'
docker run --network my_net -d redis 
docker run -v /conf:/etc/redis redis redis-server /etc/redis/redis.conf  
docker run -d -it --name test ubuntu /bin/bash

docker compose up [-d] # 启动所有compose服务,-d后台运行,前提是当前目录存在compose.yaml文件,一般用于第一次启动项目,因为此时容器不存在
docker compose restart # 对现有容器执行重新启动,容器不会被删除或重新创建
docker compose down # 停止并删除容器,网络,卷,镜像
docker compose build [--no-cache] # 构建容器
docker compose ps # 查看当前compose运行的所有容器
docker compose config # 校验并输出解析后的compose.yaml配置文件
```


