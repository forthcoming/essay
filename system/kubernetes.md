k8s是容器编排技术提供以下功能
1. 自我修复: 一旦某个容器崩溃,能在秒级启动新容器
2. 弹性伸缩: 可以根据需求,自动对集群中正在运行的容器数量进行调整
3. 服务发现: 服务可通过自己发现的形式找到他所依赖的服务
4. 负载均衡: 如果一个服务启动了多个容器,能够自动实现请求的负载均衡
5. 版本会退: 如果发现新发布程序版本有问题,可立即回退到原来版本
6. 存储编排: 可根据容器自身需求自动创建存储卷

一个k8s集群主要由控制节点(master)和工作节点(node)构成,每个节点都会安装不同组件
master: 集群控制面板,负责集群决策,组件如下
ApiServer: 资源操作唯一入口,接收用户输入命令,提供认证,授权,api注册,发现等机制
Scheduler:负责集群资源调度,按照预定的调度策略将pod调度到相应的node节点上
ControllerManager: 负责维护集群状态,比如程序部署安排,故障检测,自动扩展,滚动更新等
Etcd: 高可用的分布式Key-Value数据库,负责存储集群中各种资源对象的信息

node: 集群数据平面,负责为容器提供运行环境,组件如下
Kubelet: 负责维护容器生命周期,即通过控制docker,来创建,更新,销毁容器
KubeProxy: 负责提供集群内部服务发现和负载均衡
ContainerRuntime: 负责节点上容器的各种操作

先安装好minikube和kubectl
minikube start --image-mirror-country='cn' --image-repository='registry.cn-hangzhou.aliyuncs.com/google_containers'
minikube dashboard  # 查看控制面板
minikube status
minikube stop
minikube node add # 集群中新增节点
minikube delete # 删除本地的k8s集群
minikube ssh -n minikube # 登录节点,-n要ssh访问的节点，默认为主控制平面(建议修改docker镜像源,否则kubectl run无法拉取镜像)
minikube cp file node_name:path  # 将本地机文件拷贝到指定节点目录
minikube addons enable metrics-server # 在kube-system命名空间下开启hpa
minikube addons enable ingress # 在ingress-nginx命名空间下开启ingress
kubectl cordon|uncordon node_name # 标记node节点为不可调度|可以调度
kubectl port-forward pod_name local_port:container_port  # 将容器内应用端口映射到本机端口(调试用)
kubectl exec pod_name -c container_name -it -- /bin/sh  # 进入Pod指定容器内部执行命令
kubectl api-resources # 查看所有对象信息
kubectl explain pod # 查看对象字段的yaml文档
kubectl get node  # 查看节点信息
kubectl get all # 查看(default命名空间)所有对象信息
kubectl cp file pod_name:pod_path -c container_name # 将主机文件和目录复制到容器中或从容器中复制出来,方向是从左到右
kubectl top node|pod  # 查看资源使用详情(前提是启用metrics-server功能)
kubectl create ns dev # 创建名为dev的命名空间
kubectl delete ns dev  # 删除命名空间dev及其下所有pod
kubectl run nginx --image=nginx:alpine -n dev # 在dev(默认为default)命名空间下运行名为nginx的pod,k8s会自动拉取并运行
kubectl get pod|hpa|node|deploy|svc|ep|cj -o wide|yaml [--v=9] -w -A --show-labels  # 查看对象信息,-o显示详细信息,--v=9会显示详细的http请求,-w开启实时监控,-A查看所有命名空间
kubectl describe pod nginx -n dev # pod相关描述,通过最后的Events描述可以看到pod构建的各个细节
kubectl delete pod --all --force  # 强制删除所有pod,避免阻塞等待
kubectl logs -f pod_name -c container_name # 查看pod运行日志
kubectl edit deploy deploy_name  # 动态集群扩缩(replicas),动态镜像更新,动态自愈,每一个新版本都会新建一个ReplicaSet
kubectl rollout history deploy|ds name # 查看历史发布版本
kubectl rollout undo deploy|ds name --to-revision=1 # 回退到指定版本,默认回退到上个版本
kubectl rollout pause|resume deploy|ds name  # 暂停继续发版,金丝雀发版
kubectl label node node_name kkk=vvv  # 给节点打标签

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: dev

---

apiVersion: networking.k8s.io/v1
kind: Ingress  # 简写为ing
metadata:
  name: ing-nginx
  namespace: dev
spec:
  tls:  # 加上这部分代表https请求
    - hosts:
        - nginx.local.com
#      生成证书
#      openssl req -x509 -sha256 -nodes -days 365 -newkey rsa:2048 -keyout tls.key -out tls.crt
#      创建密钥
#      kubectl create secret tls tls-secret --key tls.key --cert tls.crt
      secretName: tls-secret # 名字需要与创建密钥名一致
  rules:  # 可以定义多个路由规则,Service的type为ClusterIP即可(NodePort也行)
    - host: nginx.local.com  # 通过该域名访问nginx,可以在本地机/etc/hosts文件添加 集群节点ip nginx.local.com 模拟
      http:  # nginx.local.com -> svc-nginx:81
        paths:
          - path: /  
            pathType: Exact # Exact完全匹配URL路径并区分大小写,Prefix基于由/分隔的URL路径前缀匹配且区分大小写
            backend:
              service:
                name: svc-nginx  # Service对象的name
                port:
                  name:  # Service对象的port名,跟下面的number二选一即可
                  number: 81  # Service对象的port号      
---

apiVersion: v1
kind: Service  # 简写为svc
metadata:
  name: svc-nginx
  namespace: dev
spec:
  selector:
    run: nginx
#  type: ClusterIP # 默认值,k8s自动分配虚拟IP,只能在集群内部访问服务,集群内节点通过ClusterIP:port访问服务,集群内Pod通过name:port访问服务
  type: NodePort # 将Service通过指定Node上的端口暴露给外部,在集群外部可通过任意节点ip:nodePort访问服务,此模式仍然保留type: ClusterIP功能
#  type: LoadBalancer # 使用外接负载均衡器完成到服务的负载分发,此模式需要外部云环境支持
#  type: ExternalName # 把集群外部的服务引入集群内部,直接使用
#  externalName: www.baidu.com # type: ExternalName下有效
  sessionAffinity: ClientIP # ClientIP相同IP访问的是同一个pod,None则忽略IP执行轮训
  ports:
    - protocol: TCP
      port: 81  # Service端口  
      targetPort: 80  # Pod端口
      nodePort: 30000 # 映射关系nodePort -> port -> targetPort,指定绑定的node端口,端口有效范围是[30000,32767],type: NodePort下生效
             
---

apiVersion: apps/v1
kind: Deployment  # 简写为deploy
metadata:
  name: deploy-nginx
  namespace: dev
spec:
  replicas: 3
  revisionHistoryLimit: 10 # 保留的历史版本,默认是10,方便版本回退
  progressDeadlineSeconds: 600 # 部署超时时间,默认600
  strategy: # 镜像更新策略
#    type: Recreate # 创建新Pod前会先杀掉所有已存在的Pod
    type: RollingUpdate # 滚动更新,杀死一部分Pod就更新一部分,即同时存在2个版本的Pod
    rollingUpdate:
      maxUnavailable: 25% # 用来指定升级过程中不可用Pod最大数量,默认25%
      maxSurge: 25% # 用来指定升级过程中不可用Pod最大数量,默认25%
  selector:
    matchLabels: # 选择Pod模板下的所有Pod
      run: nginx
  template: # Pod模板
    metadata:
      labels:
        run: nginx
    spec:
      containers:
        - name: nginx-container
          image: nginx:alpine
  
---

apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler  # 简写为hpa
metadata:
  name: hpa-nginx
  namespace: dev
spec:
  minReplicas: 1
  maxReplicas: 6
  scaleTargetRef: # 关联要控制的pod信息
    apiVersion: apps/v1
    kind: Deployment
    name: deploy-nginx
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50
        
---

apiVersion: apps/v1
kind: DaemonSet  # 简写为ds
metadata:
  name: ds-hello-world
  namespace: dev
spec:
  selector:
    matchLabels: 
      run: hello-world
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
  template: # Pod模板
    metadata:
      labels:
        run: hello-world
    spec:
      containers:
        - name: hello-world-container
          image: hello-world   
          
---

apiVersion: batch/v1
kind: Job  
metadata:
  name: job-busybox
  namespace: dev
spec:
  completions: 4 # Job需要成功运行Pod的次数,默认为1
  parallelism: 2 # Job在任意时刻并发运行Pod的数量,默认为1
  activeDeadlineSeconds: 120 # Job可运行的最长时间(所有Pod的构建和执行时间),超时未结束系统将尝试终止
  backoffLimit: 6 # Job失败后最多重试次数,默认为6
  template: # Pod模板
    metadata:
    spec:
      restartPolicy: Never # 只能是Never和OnFailure,Pod出现故障时,前者会增加失败次数,后者不增加失败次数
      containers:
        - name: busybox-container
          image: busybox   
          command: ["/bin/sh","-c","for i in 5 4 3 2 1; do echo $1; sleep 2; done"]

---

apiVersion: batch/v1
kind: CronJob  # 简写为cj
metadata:
  name: cj-busybox
  namespace: dev
spec:
  schedule: "* * * * *" # cron格式,参考Linux的crontab
  concurrencyPolicy: Allow # Allow允许Job并发运行,Forbid禁止并发运行(如果上一次运行未完成则跳过本次运行),Replace用新Job替换正在运行的Job
  failedJobsHistoryLimit: 1 # 失败任务保留的最大历史记录数,默认为1
  successfulJobsHistoryLimit: 3 # 成功任务保留的最大历史记录数(执行Job后状态为Completed的Pod个数),默认为3
  jobTemplate: # Job模板
    metadata: 
    spec:
      completions: 1
      parallelism: 1
      activeDeadlineSeconds: 120
      template: # Pod模板
        spec:
          restartPolicy: Never
          containers:
            - name: busybox-container
              image: busybox   
              command: ["/bin/sh","-c","for i in 5 4 3 2 1; do echo $1; sleep 2; done"]

---

apiVersion: v1
kind: Pod
metadata:
  name: apps
  namespace: dev
  labels:
    version: "3.0"
    env: test
spec:
  hostAliases: # 往/etc/hosts文件追加127.0.0.1 foo.local bar.local,同一个Pod下容器共享IP,所以放在containers同级定义
    - ip: "127.0.0.1"
      hostnames:
        - "foo.local"
        - "bar.local"
  containers:
    - name: python-container
      image: python:alpine
      imagePullPolicy: IfNotPresent # Always用远程,Never用本地(不是节点本地),IfNotPresent优先用本地再远程
      command: ["/bin/sh"] # 如果在配置文件中设置了容器启动时要执行的命令及其参数,容器镜像中自带的命令与参数将会被覆盖而不再执行
      args: ["-c", "while true; do echo hello; sleep 5;done"] # 如果配置文件中只是设置了参数,却没有设置其对应的命令,那么容器镜像中自带的命令会使用该新参数作为其执行时的参数
      env: # 容器环境变量列表,将覆盖容器镜像中指定的所有环境变量,可以在配置的其他地方使用
      volumeMounts: 
        - name: logs-volume  # 必须与volumes.name一致
          mountPath: /avatar  # 推荐写一个不存在的目录,k8s会自动创建
      resources:
        limits: # 限制容器运行时最大占用资源,当资源超过最大限制时会重启
          cpu: 2 # 最多2核
          memory: "10Gi" # 最大内存
        requests: # 设置容器需要的最小资源, 低于限制容器将无法启动
          cpu: 0.5
          memory: "10Mi"
    - name: redis-container
      image: redis:alpine
      volumeMounts: 
        - name: logs-volume  
          mountPath: /neos  # 推荐写一个不存在的目录,k8s会自动创建
      livenessProbe: 
        initialDelaySeconds: # 容器启动后等待多少秒执行第一次探测
        timeoutSeconds: # 探测超时时间,默认一秒
        periodSeconds: # 执行探测的频率,默认10秒
        failureThreshold: # 连续探测失败多少次才被认定为失败,默认3
        successThreshold: # 连续探测成功多少次才被认定为成功,默认1
#        exec: 
#          command: ['bin/cat','/hello.txt']
        tcpSocket:
          port: 6379  
#        httpGet:  # 访问http://127.0.0.1:80/hello
#          httpHeaders:
#            - name: Accept
#              value: application/json
#          scheme: HTTP
#          host: 127.0.0.1
#          port: 80
#          path: /hello
        
  volumes: 
    - name: logs-volume
      configMap:
        name: cm-config # 必须与ConfigMap名字一致
#      emptyDir: {}
#      hostPath:
#        path: /home/docker
#        type: DirectoryOrCreate  # 目录不存在就先创建再使用,存在则直接使用,还支持Directory|File|FileOrCreate
#      nfs: 
#        server: 192.168.2.2 # nfs服务器地址
#        path: /data # 共享文件路径
  
  nodeName:  # 将Pod调度到指定的Node节点上
  nodeSelector: # 将Pod调度到标签ssd=true的节点上
#    ssd: "true"
  restartPolicy: Always # Always容器失效时重启(默认),OnFailure容器终止运行且退出码不为0时重启, Never不重启容器,每个容器重启间隔阶梯形增长

---

apiVersion: v1
kind: ConfigMap   # 简写为cm
metadata:
  name: cm-config
  namespace: dev
data:  # key映射成文件,value映射成文件内容,如果更新了ConfigMap值,挂载目录也会动态更新
  user: oracle
  age: '12'  # 注意
```
kubectl apply -f nginx.yaml  # 创建或更新,yaml文件可以是在线文件 
kubectl delete -f nginx.yaml
kubectl get -f nginx.yaml -o yaml

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: mysql-single
  labels:
    app: mysql
spec:
  containers:
    - name: mysql-container
      image: mysql
      env:
        - name: MYSQL_ROOT_PASSWORD
          value: "123456"
      volumeMounts:
        - mountPath: /var/lib/mysql
          name: data-volume
        - mountPath: /etc/mysql/conf.d
          name: config-volume
          readOnly: true
  volumes:
    - name: config-volume
      configMap:
        name: mysql-config
    - name: data-volume
      hostPath:
        path: /mysql/data
        type: DirectoryOrCreate

---

apiVersion: v1
kind: ConfigMap  
metadata:
  name: mysql-config
data: 
  mysql.cnf: |
    [mysqld]
    bind-address = 127.0.0.1   
    datadir=/var/lib/mysql                      
    character_set_server=utf8mb4                       
    socket =/tmp/mysql.sock
        
    [client]
    socket =/tmp/mysql.sock                                
```


不同的namespace下pod无法相互访问,不同的namespace可以限制其占用的资源(如cpu,内存)
k8s集群启动时会默认创建几个namespace
kubectl get ns
default          # 所有未指定namespace的对象都会被分配在该命名空间下 
kube-node-lease  # 集群节点间的心跳维护
kube-public      # 该明明空间下的对象可以被所有人访问
kube-system      # 所有k8s创建的对象存储在该命名空间   

pod是k8s管理的最小单元,容器必须存在于pod中,一个pod可以有多个容器
k8s集群启动后集群中各个组件是以pod方式运行在kube-system命名空间下
kubectl get pod -n kube-system
NAME                               READY   STATUS    RESTARTS        AGE
coredns-65dcc469f7-m527w           1/1     Running   5 (3h31m ago)   8h
etcd-minikube                      1/1     Running   4 (7h22m ago)   8h
kube-apiserver-minikube            1/1     Running   5 (3h31m ago)   8h
kube-controller-manager-minikube   1/1     Running   5 (7h22m ago)   8h
kube-proxy-nr6wg                   1/1     Running   4 (7h22m ago)   8h
kube-scheduler-minikube            1/1     Running   4 (7h22m ago)   8h
storage-provisioner                1/1     Running   14 (32m ago)    8h

Label用于给某个对象定义标识,Label Selector用于查询和筛选拥有某些标签的资源,可以使用","分割多个组合查询,相当于and
基于等式的Label Selector: 
name=avatar选择所有Label中key=name且value=avatar的对象; name!=avatar选择所有Label中key=name且value!=avatar的对象
基于集合的Label Selector: 
name in (v1,v2)选择所有Label中key=name且value=v1或value=v2的对象; name not in (v1,v2)选择所有Label中key=name且value!=v1且value!=v2的对象
kubectl get pod -l version=3.0 -n dev # 查询指定标签的pod

Service可以看做一组同类Pod对外的访问接口,应用可以方便的实现服务发现和负载均衡
DaemonSet可以保证集群中的每个节点上运行一个副本,适用于日志收集,节点监控等,会根据集群节点数量动态增加删除Pod
Job负责批量处理短暂的一次性任务
CronJob可以在特定时间反复运行Job任务
Endpoint存储在Etcd中,用来记录一个Service对应的所有Pod访问地址,它是根据Service配置中的selector描述产生的
ResourceQuota限制命名空间中所有Pod|CronJob等的运行总数、内存请求总量、内存限制总量、CPU请求总量、CPU限制总量
LimitRange限制命名空间中单个Pod的内存请求总量、内存限制总量、CPU请求总量、CPU限制总量
服务质量类(QoS class)包括Guaranteed,Burstable,BestEffort,k8s在Node资源不足时使用QoS类来就驱逐Pod作出决定

Volume是Pod中能被多个容器访问的共享目录,定义在Pod上,k8s通过Volume实现同一个Pod中不同容器间数据共享和数据持久化存储
Volume生命周期不与Pod中单个容器生命周期相关,容器终止或重启时Volume数据不丢失,Volume常见类型如下:
EmptyDir: 创建Pod时创建,初始内容为空,Pod销毁时EmptyDir中数据也被删除
HostPath: 将节点中一个实际目录挂在到Pod中,Pod销毁时数据依旧存在节点上,缺点是Pod挂掉后可能会在其他节点新建Pod,导致数据失效
NFS: 网络文件存储系统,所有Pod数据都存储到这个上面
ConfigMap: 存储配置信息的存储卷
Secret: 用法与ConfigMap类似,存储敏感信息

容器探测用于检测容器中应用是否正常工作,k8s提供2种探针实现容器探测
livenessProbe: 存活性探针,用于检测应用实例当前是否处于正常运行状态,如果不是,k8s会重启容器,由Pod的重启策略restartPolicy决定
startupProbe: 启动探针,应用有最多t=failureThreshold * periodSeconds的时间来完成其启动过程
一旦启动探测成功一次,存活探测任务就会接管对容器的探测,如果启动探测一直没成功,容器会在t秒后被杀死,并且根据restartPolicy来执行进一步处置
readinessProbe: 就绪性探针,用于检测应用实例当前是否可以接受请求,如果不能,k8s不会转发流量但不会重启容器,就绪探针在容器的整个生命周期中保持运行状态
探针支持以下三种方式
Exec: 在容器内执行一次命令,如果命令执行退出码为0,则认为程序正常
TCPSocket: 尝试访问一个用户容器端口,如果能建立连接,则认为程序正常
HTTPGet: 调用容器内web应用的url,如果返回状态码在200-399之间,则认为程序正常

YAML是JSON的超集,支持整数、浮点数、布尔、字符串、数组和对象等数据类型,大小写敏感,任何合法的JSON文档也都是YAML文档
使用空白与缩进表示层次
使用 # 书写注释
使用 - 开头表示数组
使用 | 表示多行文本块
使用 : 表示对象,格式与JSON基本相同,但Key不需要双引号
使用 --- 在一个文件里分隔多个YAML对象
表示对象的 : 和表示数组的 - 后面都必须有空格
