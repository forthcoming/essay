### common

```
docker0是docker在主机虚拟出的网桥,使用ifconfig或ip address查看,镜像产生的容器IP位于该网段,苹果电脑下无法创建docker0网桥,所以宿主机无法ping通容器
构建Dockerfile或者docker pull拉下来的叫镜像, 运行中的镜像叫容器,同一个镜像可以实例化多个容器
容器内访问外部服务用的ip是宿主机ip
docker建议每个容器只运行一个服务
每个虚拟机都是独立的环境,容器共享操作系统,占用资源更少
mac系统docker desktop在engine设置页面新增:
"registry-mirrors": ["https://yxzrazem.mirror.aliyuncs.com","http://hub-mirror.c.163.com"]
centos系统修改如下:
sudo vi /etc/docker/daemon.json
"registry-mirrors": ["https://yxzrazem.mirror.aliyuncs.com","http://hub-mirror.c.163.com"]
sudo systemctl restart docker
sudo dockerd # 启动dockerd服务
```

### docker命令

```shell
docker info # 查看docker相关信息
docker pull image_name[:tag] # 拉镜像,如果不指定tag,默认值是latest
docker images [-a|--no-trunc]  # 查看本地镜像列表,-a显示所有镜像(默认隐藏中间镜像),--no-trunc意思是不要截断输出
docker search [--no-trunc] nginx  # 搜索docker hub中的镜像
docker system df # 查看镜像,容器,数据卷占用空间
docker rmi [-f] image_id|image_name[:tag] # 删除镜像,如果镜像对应的容器正在运行则无法删除,需先stop再-f强制删除
docker commit [-a 'author'|-m 'the first image'] container_id image_name[:tag] # 保存已经更改的容器为新镜像
docker login # 登陆
docker push yourname/image_name[:tag] # 推送本地镜像到远程仓库,需提前用docker login账户创建好仓库
docker tag old_image_name[:tag] yourname/image_name[:tag] # 给原镜像打标签,产生的新镜像跟之前的镜像是同一个image_id
docker build [--no-cache] -t image_name[:tag] [-f dir/Dockerfile] .  # 构建镜像,不指定-f则默认为当前目录下名为Dockerfile的文件
docker network ls   # 查看docker网络模式,容器默认使用桥接网络
docker network inspect brideg_name   # 查看网络详情(包含哪些容器使用当前网络)
docker network create network_name  # 默认创建的是桥接网络
docker history [--no-trunc] image_name[:tag] # 逆序查看镜像构建语句
docker compose up [-d] # 启动所有compose服务,-d后台运行,前提是当前目录存在compose.yaml文件
docker compose down # 停止并删除容器,网络,卷,镜像
docker compose build [--no-cache] # 构建容器
docker compose ps # 查看当前compose运行的所有容器
docker compose config # 校验并输出解析后的compose.yaml配置文件
docker save/load image_name # 保存加载镜像
docker export/import container_name # 导出导入容器

docker ps [-a] # 查看正在运行的容器(也可以查看容器的映射端口),-a查看所有容器
docker top [container_name|container_id]  # 查看容器负载情况(pid并非容器内进程的pid)
docker rm [-f] container_name|container_id  # 删除已经停止的容器,-f强制删除容器
docker start container_name|container_id # 启动已经停止的容器
docker restart container_name|container_id # 重启正在运行的容器
docker stop container_name|container_id # 停止正在运行的容器
docker attach container_name|container_id  # 进入正在运行的容器终端
docker exec container_name|container_id cmd  # 在运行中的容器中启动新进程,在容器环境执行命令并显示,如docker exec -it redis /bin/bash
docker kill container_name|container_id # 强制停止容器
docker logs [-tf] container_name|container_id # 查看容器控制台输出日志,-f参考linux的tail,-t显示时间戳
docker inspect image_id|container_id  # 查看镜像或容器的详细信息,只有启动的容器才分配IP,IP保存在IPAddress字段
docker cp container_name|container_id:container_path source_path # 拷贝容器中的文件到本机
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
```


