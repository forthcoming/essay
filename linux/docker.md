```pycon
docker默认是允许container互通,通过-icc=false关闭互通
一旦关闭了互通,只能通过-link name:alias命令连接指定container.
docker0是docker虚拟出来的一个网桥,镜像产生的容器IP位于该网段
容器只有启动了,才会查看到他的IP
[root@local Desktop]# brctl addbr docker   #给docker自定义一个虚拟网桥（重启会失效）
[root@local Desktop]# ifconfig docker 192.168.9.100 netmask 255.255.255.0
[root@local Desktop]# docker inspect -f {{.NetworkSettings.IPAddress}} test  #通用模板是{{.aa.bb.cc}}
192.168.9.1
```

### 加速訪問鏡像,并配置远程访问docker,自定义网桥
```shell
[root@local ~]# more /etc/sysconfig/network-scripts/ifcfg-docker  #自定义网桥
DEVICE=docker
ONBOOT=yes
BOOTPROTO=dhcp
TYPE=Bridge

[root@local ~]# more /usr/lib/systemd/system/docker.service
[Unit]
Description=Docker Application Container Engine
Documentation=https://docs.docker.com
After=network.target docker.socket
Requires=docker.socket

[Service]
Type=notify
ExecStart=/usr/bin/docker daemon --registry-mirror=http://aad0405c.m.daocloud.io -H 0.0.0.0:6666 -H unix:///var/run/docker.sock -b=docker
MountFlags=slave
LimitNOFILE=1048576
LimitNPROC=1048576
LimitCORE=infinity
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
[root@local ~]# ps -ef|grep docker
root     15654     1  0 09:43 ?        00:00:00 /usr/bin/docker daemon --registry-mirror=http://aad0405c.m.daocloud.io -H 0.0.0.0:6666 -H unix:///var/run/docker.sock
root     15780 15509  0 09:45 pts/1    00:00:00 grep --color=auto docker

注意：
远程访问
docker -H tcp://192.168.9.8:6666 images
export DOCKER_HOST=tcp://192.168.9.8:6666 && docker images
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
[root@local Desktop]#
```

### docker安装
```pycon
curl -fsSL https://get.docker.com/ | sh
curl -sSL https://get.daocloud.io/docker | sh
http://get.daocloud.io/docker/builds/
yum install docker也行,但不是最新版
```

```pycon
systemctl start docker
docker pull scrapinghub/splash
docker images [-a|-q|--no-trunc]
docker ps      #查看正在运行的容器（也可以查看容器的映射端口）
docker ps -a   #查看历史运行的容器
docker run -p 80:80 -v /usr/local/data:/container/data --name=test scrapinghub/splash  #查看历史运行的容器
docker run -w centos echo 'Hello' #-w指定工作目录，及进入时的目录（相当于帮你做了cd操作），一般设置为安装软件目录，他会覆盖dockerfile中的WORKDIR

docker run -it centos /bin/bash
docker exec -it test /bin/bash  #在运行中的容器中启动新进程
ctrl+p & ctrl+q  #就会使上条命令在后台运行
docker attach 2d60f4071054  #再次进入后台运行的命令

docker build -t myos:first .  #构建自己的Dockerfile
docker top test  #查看容器开启的进程
docker inspect test  #既可以查看镜像，也可以查看容器
docker start -i test     #重新启动已经停止的容器
docker rm test           #删除已经停止的容器
docker rm -f test        #强制删除容器
docker stop test         #等待容器停止
docker kill test         #强制使容器停止
docker history --no-trunc test     #查看容器构建过程
docker rmi  centos #删除镜像
docker logs -tf --tail 10 test
docker cp  web:/usr/local/nginx .    #拷贝容器中的文件到本机
/var/lib/docker    #docker镜像存储目录
docker search [-s 30] nginx  #在线搜索docker hub中的镜像
docker login
docker tag ubuntu:14.04 ooxxme/myubuntu:last  #给原镜像打标签，产生的新镜像跟之前的镜像是同一个ID
docker push yourname/imagename     #必须以自己的名字开头

docker commit [-a 'Author'|-m 'the first image'] 8d93082a9ce1 ubuntu:myubuntu #保存已经更改的容器为新镜像
docker save -o myubuntu.tar ubuntu:myubuntu   #保存的文件名可以不以.tar结尾，仅仅是个后缀名而已
docker save ubuntu:myubuntu> myubuntu.tar     #等价于上一句
docker load -i myubuntu.tar
docker load < myubuntu.tar                #等价于上一句
docker import myubuntu.tar        #导入官方的原生镜像

构建Dockerfile或者docker pull拉下来的叫镜像, 运行中的镜像叫容器
docker pull repo_name  # 拉镜像,同一个镜像可以实例化多个容器
docker build -t name:tag -f dir/Dockerfile .  # 构建镜像
docker images    # 查看本地镜像列表
docker ps -a   # 查看正在运行的容器和运行后退出的容器
docker rm -f container_id|container_name   # 删除容器
docker rmi -f image_id   # 删除镜像(如果镜像对应的容器正在运行则无法删除,需先stop再-f强制删除)
docker inspect image_id|container_id  # 查看镜像或容器的详细信息
docker inspect --format='{{.NetworkSettings.IPAddress}}' container_id  # 查看容器ip(针对容器不含ifconfig命令)
docker容器ip跟宿主机不一样,但容器内访问外部服务用的ip是宿主机ip
docker stop container_id   # 关闭正在运行的容器
docker exec -it container_id cmd  # 在容器环境执行命令并显示,进入到容器内部使用sh
docker logs -f container_id   # 查看容器控制台输出日志,比如Dockerfile中CMD ["ping","127.0.0.1"],和tail -f类似
docker network ls   # 容器默认使用的是桥接网络
docker network create my_net  # 默认创建的是桥接网络
docker inspect my_net
docker tag redis YOUR-USER-NAME/redis:latest   # rename, If you don’t specify a tag, Docker will use a tag called latest. 需提前在dockerhub创建好仓库
docker push akatsuki404/all-in-one:tagname

docker run --network my_net --name test_net -d redis   # 使用自定义网桥,容器之间可通过容器名互连,默认的bridge只能通过ip互连,互连前提是位于同一个网络
docker run -dp 90:80 image_id  # d means run the container in detached mode (in the background),p 80:80 means map port 80 of the host to port 80 in the container,可通过宿主机ip+宿主机端口90访问容器80端口程序
docker run -dit --rm --name local image_id # 容器运行不退出,如果本地镜像不存在,会先去dockerhub拉取镜像
docker run -v /conf:/etc/redis redis redis-server /etc/redis/redis.conf  # 容器目录不存在会创建,存在则覆盖,改动本机或容器,则另一端目录内容也会改变.The mapped directory should be writable
--add-host list                  Add a custom host-to-IP mapping (host:ip)
--attach list                    Attach to STDIN, STDOUT or STDERR
--cpus decimal                   Number of CPUs
--detach                         Run container in background and print container ID
--entrypoint string              Overwrite the default ENTRYPOINT of the image
--env list                       Set environment variables
--expose list                    Expose a port or a range of ports
--hostname string                Container host name
--ip string                      IPv4 address (e.g., 172.30.100.104)
--ip6 string                     IPv6 address (e.g., 2001:db8::33)
--mac-address string             Container MAC address (e.g., 92:d0:c6:0a:29:33)
--memory bytes                   Memory limit
--mount mount                    Attach a filesystem mount to the container
--name string                    Assign a name to the container
--network network                Connect a container to a network
--pids-limit int                 Tune container pids limit (set -1 for unlimited)
--pull string                    Pull image before running ("always"|"missing"|"never") (default "missing")
--read-only                      Mount the container's root filesystem as read only
--restart string                 Restart policy to apply when a container exits (default "no")
--rm                             Automatically remove the container when it exits
--runtime string                 Runtime to use for this container
--stop-signal string             Signal to stop a container (default "SIGTERM")
--stop-timeout int               Timeout (in seconds) to stop a container
--tty                            Allocate a pseudo-TTY
--ulimit ulimit                  Ulimit options (default [])
--user string                    Username or UID (format: <name|uid>[:<group|gid>])
--volume list                    Bind mount a volume
--workdir string                 Working directory inside the container
```




