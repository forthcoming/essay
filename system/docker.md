```shell
docker pull image_name[:tag] # 拉镜像,如果不指定tag,默认值是latest
docker images [-a|--no-trunc]  # 查看本地镜像列表,-a显示所有镜像(默认隐藏中间镜像),--no-trunc意思是不要截断输出
docker search [--no-trunc] nginx  # 搜索docker hub中的镜像
docker system df # 查看镜像,容器,数据卷占用空间
docker rmi [-f] image_id|image_name[:tag] # 删除镜像,如果镜像对应的容器正在运行则无法删除,需先stop再-f强制删除
docker commit [-a 'author'|-m 'the first image'] container_id image_name[:tag] # 保存已经更改的容器为新镜像
docker login # 登陆
docker push yourname/image_name[:tag] # 推送本地镜像到远程仓库,需提前用docker login账户创建好仓库
docker tag old_image_name[:tag] yourname/image_name[:tag] # 给原镜像打标签,产生的新镜像跟之前的镜像是同一个image_id

docker ps [-a] # 查看正在运行的容器(也可以查看容器的映射端口),-a查看所有容器
docker top [container_name|container_id]  # 查看容器负载情况
docker rm [-f] container_name|container_id  # 删除已经停止的容器,-f强制删除容器
docker start container_name|container_id # 启动已经停止的容器
docker stop container_name|container_id # 停止正在运行的容器
docker attach container_name|container_id  # 进入正在运行的容器终端
docker exec container_name|container_id cmd  # 在运行中的容器中启动新进程,在容器环境执行命令并显示
docker kill container_name|container_id # 强制停止容器
docker logs [-tf] container_name|container_id # 查看容器控制台输出日志,-f参考linux的tail,-t显示时间戳
docker inspect image_id|container_id  # 查看镜像或容器的详细信息
docker inspect -f {{.NetworkSettings.IPAddress}} container_id  # 查看容器ip,通用模板是{{.aa.bb.cc}}
docker cp container_name|container_id:container_path source_path # 拷贝容器中的文件到本机
ctrl+p & ctrl+q # 退出容器
exit # 退出容器并停止容器

docker run image_id  # 运行本地镜像,如果镜像不存在,会先去dockerhub拉取镜像
--name: 指定容器名称
-d: 后台运行容器并打印容器id
-i: 以交互模式运行容器(通常与-t同时使用)
-t: 为容器分配一个终端
-p: 宿主机:容器端口映射,可通过宿主机ip:port访问容器指定port程序
-v: 宿主机:容器目录映射,容器目录不存在会创建,存在则覆盖,改动本机或容器,则另一端目录内容也会改变
--rm: 容器退出时自动删除
-m: 以bytes为单位容器最大内存
-w: 容器工作目录,即进入时的目录,相当于执行cd操作,一般设置为安装软件目录,他会覆盖dockerfile中的WORKDIR
docker run -p 80:80 -v /usr/local/data:/container/data --name=test centos echo 'Hello'
docker run --network my_net --name test_net -d redis # 使用自定义网桥,容器之间可通过容器名互连,默认的bridge只能通过ip互连,互连前提是位于同一个网络
docker run -v /conf:/etc/redis redis redis-server /etc/redis/redis.conf  
docker run -it centos /bin/bash
docker build -t myos:first .  # 构建自己的Dockerfile
docker build -t name:tag -f dir/Dockerfile .  # 构建镜像
docker history --no-trunc test # 查看容器构建过程
docker network ls   # 容器默认使用的是桥接网络
docker network create my_net  # 默认创建的是桥接网络
构建Dockerfile或者docker pull拉下来的叫镜像, 运行中的镜像叫容器,同一个镜像可以实例化多个容器
容器ip跟宿主机不一样,但容器内访问外部服务用的ip是宿主机ip
```

```shell
[root@local Desktop]# docker ps
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS                    NAMES
9c730600518f        redis               "/entrypoint.sh /bin/"   About an hour ago   Up About an hour    0.0.0.0:1234->6379/tcp   cocky_leavitt
[root@local Desktop]# docker top cocky_leavitt
UID                 PID                 PPID                C                   STIME               TTY                 TIME                CMD
root                17567               6181                0                   10:48               pts/2               00:00:00            /bin/bash
root                17775               17567               0                   10:51               ?                   00:00:04            redis-server *:6379
[root@local Desktop]# docker exec cocky_leavitt ps -ef
UID        PID  PPID  C STIME TTY          TIME CMD
root         1     0  0 02:48 ?        00:00:00 /bin/bash
root        18     1  0 02:51 ?        00:00:04 redis-server *:6379
root        37     0  0 03:51 ?        00:00:00 ps -ef
[root@local Desktop]# ps -ef|grep redis
UID        PID  PPID  C STIME TTY          TIME CMD
root     17775 17567  0 10:51 ?        00:00:04 redis-server *:6379
root     18662 18590  0 11:51 pts/0    00:00:00 grep --color=auto redis
[root@local Desktop]# netstat -anp|grep 1234
Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name
tcp6       0      0 :::6666                 :::*                    LISTEN      6181/docker
tcp6       0      0 :::1234                 :::*                    LISTEN      17562/docker-proxy
[root@local Desktop]# netstat -anp|grep redis
```

```
curl -fsSL https://get.docker.com | sh    # 安装docker
docker默认是允许container互通,通过-icc=false关闭互通,一旦关闭了互通,只能通过-link name:alias命令连接指定container
docker0是docker虚拟出来的一个网桥,镜像产生的容器IP位于该网段,容器只有启动了,才会查看到他的IP
[root@local Desktop]# brctl addbr docker   #给docker自定义一个虚拟网桥（重启会失效）
[root@local Desktop]# ifconfig docker 192.168.9.100 netmask 255.255.255.0
apt-get update    
apt-get install vim
```
