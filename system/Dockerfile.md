```pycon
# 可以是任何一个存在的镜像(类似套娃)
# Alpine Linux is much smaller than most distribution base images (~5MB), and thus leads to much slimmer images in general.
# The main caveat to note is that it does use musl libc instead of glibc and friends, so software will often run into issues depending on the depth of their libc requirements/assumptions. 
FROM python:3.9-alpine   

ENV REDIS_DOWNLOAD_URL http://download.redis.io/releases/redis-6.2.4.tar.gz
RUN apk upgrade; \
    wget -O redis.tar.gz "$REDIS_DOWNLOAD_URL"; \
    mkdir -p /usr/src/redis; \
    tar -xzf redis.tar.gz -C /usr/src/redis --strip-components=1; \
    rm redis.tar.gz;

# The CMD directive specifies the default command to run when starting a container from this image.
CMD ["python"]  


#RUN mkdir /data && chown redis:redis /data
#VOLUME /data
#WORKDIR /data

#COPY docker-entrypoint.sh /usr/local/bin/
#ENTRYPOINT ["docker-entrypoint.sh"]

#EXPOSE 6379
#CMD ["redis-server"] 
```


```pycon
from ubuntu:14.04
maintainer akatsuki 212956978@qq.com
run apt-get install -y nginx && mkdir ~/fuck
#复制宿主机文件到容器中
copy test.py ~/fuck/door.txt
#指定的端口会在容器运行时显示出来
expose 80 3306
```

```pycon
FROM centos6-base
MAINTAINER zhou_mfk <zhou_mfk@163.com>
RUN ssh-keygen -q -N "" -t dsa -f /etc/ssh/ssh_host_dsa_key
RUN ssh-keygen -q -N "" -t rsa -f /etc/ssh/ssh_host_rsa_key
RUN sed -ri 's/session    required     pam_loginuid.so/#session    required     pam_loginuid.so/g' /etc/pam.d/sshd
RUN mkdir -p /root/.ssh && chown root.root /root && chmod 700 /root/.ssh
EXPOSE 22
RUN echo 'root:redhat' | chpasswd
RUN yum install tar gzip gcc vim wget -y
ENV LANG en_US.UTF-8
CMD /usr/sbin/sshd -D
```