# 可以是任何一个存在的镜像(类似套娃)
# Alpine Linux is much smaller than most distribution base images (~5MB), and thus leads to much slimmer images in general.
# The main caveat to note is that it does use musl libc instead of glibc and friends, so software will often run into issues depending on the depth of their libc requirements/assumptions. 
FROM python:3.9-alpine   

ENV REDIS_DOWNLOAD_URL http://download.redis.io/releases/redis-6.2.4.tar.gz
RUN wget -O redis.tar.gz "$REDIS_DOWNLOAD_URL"; \
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

