### 简介
```
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

集群下节点间是互通的,节点可以访问集群上的任意pod,同一个节点下的pod间互通
```

### yaml用法
```
YAML是JSON的超集,支持整数、浮点数、布尔、字符串、数组和对象等数据类型,大小写敏感,任何合法的JSON文档也都是YAML文档
使用空白与缩进表示层次
使用 # 书写注释
使用 - 开头表示数组
使用 | 表示多行文本块
使用 : 表示对象,格式与JSON基本相同,但Key不需要双引号
使用 --- 在一个文件里分隔多个YAML对象
表示对象的 : 和表示数组的 - 后面都必须有空格
```

### namespace
```
不同的namespace下pod无法相互访问,不同的namespace可以限制其占用的资源(如cpu,内存)
k8s集群启动时会默认创建几个namespace
kubectl get ns
default          # 所有未指定namespace的对象都会被分配在该命名空间下 
kube-node-lease  # 集群节点间的心跳维护
kube-public      # 该明明空间下的对象可以被所有人访问
kube-system      # 所有k8s创建的对象存储在该命名空间
```

### pod
```
pod是k8s管理的最小单元,容器必须存在于pod中,一个pod可以有多个容器
pod下所有容器共享pod的ip和端口,pod每次重启ip都不一样
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
```

### 探测器
```
容器探测用于检测容器中应用是否正常工作,k8s提供2种探针实现容器探测
livenessProbe: 存活性探针,用于检测应用实例当前是否处于正常运行状态,如果不是,k8s会重启容器,由Pod的重启策略restartPolicy决定
startupProbe: 启动探针,应用有最多t=failureThreshold * periodSeconds的时间来完成其启动过程,此探针成功前会禁用所有其他探针
启动探测成功后其他探测任务就会接管对容器的探测,如果启动探测一直没成功,容器会在t秒后被杀死,并且根据restartPolicy来执行进一步处置
readinessProbe: 就绪性探针,用于检测应用实例当前是否可以接受请求,如果不能,k8s不会转发流量但不会重启容器,就绪探针在容器的整个生命周期中保持运行状态
探针支持以下三种方式
Exec: 在容器内执行一次命令,如果命令执行退出码为0,则认为程序正常
TCPSocket: 尝试访问一个用户容器端口,如果能建立连接,则认为程序正常
HTTPGet: 调用容器内web应用的url,如果返回状态码在200-399之间,则认为程序正常
```

### label
```
Label用于给某个对象定义标识,Label Selector用于查询和筛选拥有某些标签的资源,可以使用","分割多个组合查询,相当于and
基于等式的Label Selector: 
name=avatar选择所有Label中key=name且value=avatar的对象; name!=avatar选择所有Label中key=name且value!=avatar,或没有key=name标签的对象
基于集合的Label Selector: 
name in (v1,v2)选择所有Label中key=name且value=v1或value=v2的对象; name notin (v1,v2)选择所有Label中key=name且value!=v1且value!=v2的对象
partition选择所有包含了有partition标签的资源,没有校验它的值; !partition选择所有没有partition标签的资源,没有校验它的值
kubectl get pod -l version=3.0 -n dev # 查询指定标签的pod
```

### volume
```
Volume是Pod中能被多个容器访问的共享目录,定义在Pod上,k8s通过Volume实现同一个Pod中不同容器间数据共享和数据持久化存储
Volume生命周期不与Pod中单个容器生命周期相关,容器终止或重启时Volume数据不丢失,Volume常见类型如下:
EmptyDir: 创建Pod时创建,初始内容为空,Pod销毁时EmptyDir中数据也被删除
HostPath: 将节点中一个实际目录挂在到Pod中,Pod销毁时数据依旧存在节点上,缺点是Pod挂掉后可能会在其他节点新建Pod,导致数据失效
NFS: 网络文件存储系统,所有Pod数据都存储到这个上面
ConfigMap: 存储配置信息的存储卷
Secret: 用法与ConfigMap类似,存储敏感信息
```

### 其他对象
```
Service可以看做一组同类Pod对外的访问接口,应用可以方便的实现服务发现和负载均衡
DaemonSet可以保证集群中的每个节点上运行一个副本,适用于日志收集,节点监控等,会根据集群节点数量动态增加删除Pod
Job负责批量处理短暂的一次性任务
CronJob可以在特定时间反复运行Job任务
Endpoint存储在Etcd中,用来记录一个Service对应的所有Pod访问地址,它是根据Service配置中的selector描述产生的
ResourceQuota限制命名空间中所有Pod|CronJob等的运行总数、内存请求总量、内存限制总量、CPU请求总量、CPU限制总量
LimitRange限制命名空间中单个Pod的内存请求总量、内存限制总量、CPU请求总量、CPU限制总量
服务质量类(QoS class),当Node没有足够可用资源时按照BestEffort > Burstable > Guaranteed优先级驱逐Pod
```

### ingress安装技巧
```shell
# 插件开启失败时解决方案
minikube addons enable metrics-server
kubectl get pod,svc -o wide -n kube-system
minikube ssh 
docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/metrics-server 
kubectl edit deploy metrics-server -n kube-system  # 修改imagePullPolicy,image,nodeName属性
```

### ingress原理剖析
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ingress-nginx-controller
  namespace: ingress-nginx
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: ingress-nginx
  template:
    metadata:
      labels:
        app.kubernetes.io/name: ingress-nginx
    spec:
      containers:
        image: registry.cn-hangzhou.aliyuncs.com/google_containers/nginx-ingress-controller:v1.8.1
        name: controller
        ports:
        - containerPort: 80  # 容器监听的端口
          hostPort: 80  # 容器端口映射到所在节点的端口,如果设置,主机只能运行一个容器副本即replicas: 1,区别与kubectl port-forward
          name: http
          protocol: TCP
        - containerPort: 443
          hostPort: 443
          name: https
          protocol: TCP
        - containerPort: 8443
          name: webhook
          protocol: TCP
        livenessProbe:
          failureThreshold: 5
          httpGet:
            path: /healthz
            port: 10254
            scheme: HTTP
          initialDelaySeconds: 10
          periodSeconds: 10
          successThreshold: 1
          timeoutSeconds: 1
        readinessProbe:
          failureThreshold: 3
          httpGet:
            path: /healthz
            port: 10254
            scheme: HTTP
          initialDelaySeconds: 10
          periodSeconds: 10
          successThreshold: 1
          timeoutSeconds: 1
---

apiVersion: v1
kind: Service
metadata:
  name: ingress-nginx-controller
  namespace: ingress-nginx
spec:
  selector:
    app.kubernetes.io/name: ingress-nginx
  type: NodePort
  clusterIP: 10.104.132.85
  ports:
  - appProtocol: http
    name: http
    nodePort: 30676
    port: 80
    protocol: TCP
    targetPort: http
  - appProtocol: https
    name: https
    nodePort: 31344
    port: 443
    protocol: TCP
    targetPort: https
    
# ingress插件会运行一个包含nginx和控制器的Pod
# Ingress对象中定义的rules会被控制器映射到nginx的/etc/nginx/nginx.conf文件
# 所以rules中的域名请求会被nginx转发到对应的Service对象上去
```

# 常用命令(先安装好minikube和kubectl)
```shell
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
kubectl cp local_path pod_name:pod_path -c container_name # 将主机文件和目录复制到容器中或从容器中复制出来,方向是从左到右
kubectl top node|pod  # 查看资源使用详情(前提是启用metrics-server功能)
kubectl create ns dev # 创建名为dev的命名空间
kubectl delete ns dev  # 删除命名空间dev及其下所有pod
kubectl run nginx --image=nginx:alpine -n dev # 在dev(默认为default)命名空间下运行名为nginx的pod,k8s会自动拉取并运行
kubectl get pod|hpa|node|deploy|svc|ep|cj -o wide|yaml [--v=9] -w -A --show-labels  # 查看对象信息,-o显示详细信息,--v=9会显示详细的http请求,-w开启实时监控,-A查看所有命名空间
kubectl describe pod nginx -n dev # pod相关描述,通过最后的Events描述可以看到pod构建的各个细节
kubectl delete pod --all --force  # 强制删除所有pod,避免阻塞等待
kubectl logs -f pod_name -c container_name # 查看pod运行日志
kubectl edit deploy deploy_name  # 动态集群扩缩(replicas),动态镜像更新,动态自愈,每一个新版本都会新建一个ReplicaSet
kubectl edit ingress ingress_name # 相当于kubectl get ing my-ing -o yaml > ing.yaml && vi ing.yaml && kubectl apply -f ing.yaml
kubectl rollout history deploy|ds name # 查看历史发布版本
kubectl rollout undo deploy|ds name --to-revision=1 # 回退到指定版本,默认回退到上个版本
kubectl rollout pause|resume deploy|ds name  # 暂停继续发版,金丝雀发版
kubectl label node|pod name kkk=vvv --overwrite # 给对象打标签,overwrite代表更新
kubectl label node|pod name kkk- # 删除对象标签
kubectl apply -f nginx.yaml  # 创建或更新 
kubectl delete -f nginx.yaml
kubectl get -f nginx.yaml -o yaml
kubectl replace -f https://k8s.io/examples/application/nginx/nginx-deployment.yaml --force # 删除并重新创建资源
```

### 资源配置样例
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: dev

---

apiVersion: v1
kind: Secret
type: kubernetes.io/tls
metadata:
  name: tls-secret  # 等价于kubectl create secret tls tls-secret --key tls.key --cert tls.crt
  namespace: dev
data: 
  # 生成证书
  # openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout tls.key -out tls.crt -subj "/CN=my-nginx/O=my-nginx"
  # 对密钥实施base64编码
  # cat tls.crt | base64 
  # cat tls.key | base64   
  tls.crt: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUNsakNDQVg0Q0NRQzhrUHI4enNoZi9EQU5CZ2txaGtpRzl3MEJBUXNGQURBTk1Rc3dDUVlEVlFRR0V3SmoKYmpBZUZ3MHlNekE1TVRBeE1EQTRNemRhRncweU5EQTVNRGt4TURBNE16ZGFNQTB4Q3pBSkJnTlZCQVlUQW1OdQpNSUlCSWpBTkJna3Foa2lHOXcwQkFRRUZBQU9DQVE4QU1JSUJDZ0tDQVFFQTBDUnlsQm1sUk9HUG5HZVBjL1BSCmk2cVBkVmdzYWUxdE42R0RUMktWTkhUVHFSMUkyOUIrTm9MNGlFOGJaUlp5ZTJtWGdsaEJBODhlZjJsS0o1N3UKdnJudDJFeHR0MHBpcGFNYk93a3Nrd1ZoOUpyQ0tkMDFzd3R5ZkpGdE9pRE4rNmMxOUhFRzdXazJJVEdjOWFkOQo0SEJ0ZnRtODNKc0RGUFlmdkVWRmxnaDV1ZlQydHNCL2VVMytONHFTYncybjExY3huSjdlZGY1OU5uVUFqRzNNCmljamNWdllidDh0WHUxbko4d3FQWjFCMDNDbWZYbW1Va3hkSEpTUkp4NTdvQitYV3U0UGloa2ZwSyt3bEhlelkKV3lDMmhlcWZpelRqUjYzeDM2R2piZXVBZmRLdkYxYnk4anR4dVRxQWVMUUFTZ0VBU2VkeW1UQTVUT05lbjRxTwp6d0lEQVFBQk1BMEdDU3FHU0liM0RRRUJDd1VBQTRJQkFRQmUwVE55WVpzWXlBWlN3TFgwNVhhVXU5VlYxSjdLCktpaEUyc2ZMVlRrZVFDUnpkVVBSQm5CaXRjRnlZSDVRN0h3REdtL2NUMGtPZmM3TElJc3loaEJKemhpMVY2SGIKUElMODlUN2g1NDFOcmRpNTlFWlBWRXFOd1hNSnNlSjAxWlYrckJIaldURDQ1MWJ6OEpUN0Z1T1lPWGN4NGtDdQpVcWkyWVBTandnR3BZbFZoQnB0VHVRMGI4VGhCRVR6L2pBTFZSdHFWSllqYVVrazgwSlpxQTJsalBBaUVmZFhKCkNHdU0rUmNTdDFVeURzT2drT3BlS2Q5cUJPclROS2VwRmhJZms4cSt2VEJHMm9xZWUrVmNFQXJUT2JlSUJQRHAKcldvR1Q5RHRqREJDWFFHa3J4aWJRWFo0VzBJOXVhbnRkVEdaaUUyWlZrWGtkcE5BeU9vZTg1eHMKLS0tLS1FTkQgQ0VSVElGSUNBVEUtLS0tLQo=
  tls.key: LS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0tCk1JSUV2UUlCQURBTkJna3Foa2lHOXcwQkFRRUZBQVNDQktjd2dnU2pBZ0VBQW9JQkFRRFFKSEtVR2FWRTRZK2MKWjQ5ejg5R0xxbzkxV0N4cDdXMDNvWU5QWXBVMGROT3BIVWpiMEg0Mmd2aUlUeHRsRm5KN2FaZUNXRUVEeng1LwphVW9ubnU2K3VlM1lURzIzU21LbG94czdDU3lUQldIMG1zSXAzVFd6QzNKOGtXMDZJTTM3cHpYMGNRYnRhVFloCk1aejFwMzNnY0cxKzJiemNtd01VOWgrOFJVV1dDSG01OVBhMndIOTVUZjQzaXBKdkRhZlhWekdjbnQ1MS9uMDIKZFFDTWJjeUp5TnhXOWh1M3kxZTdXY256Q285blVIVGNLWjllYVpTVEYwY2xKRW5IbnVnSDVkYTdnK0tHUitrcgo3Q1VkN05oYklMYUY2cCtMTk9OSHJmSGZvYU50NjRCOTBxOFhWdkx5TzNHNU9vQjR0QUJLQVFCSjUzS1pNRGxNCjQxNmZpbzdQQWdNQkFBRUNnZ0VBQlFsOHhGekNoU0k0U1g2d0dBeEVlKzdLdmZvK1NPbjRCS3FoOU4vYjRJTWIKUkRKek91Nld2MWI0RU1ScFUwN3h3azdSM2RPbzd5Q3FDa2RRQmhsd2lha1NPblBQQytwKzdLYy8xM1BuWWo5MQpHV2hOWHBuOTNMRmdPZWVERHk4UURSRUUyeitJL1dIWWI0RTEzVFFLZGM0Q3VGa29tdVlkY3ZwcDFqS085b3grCnZzL1hwNnJxYit1cmtNTXZYY3hxTWk3NVlTTzEzdEl1Vzg5S3JIbHU3WDhnOUN5dHIzSGQrQnNXUG1BYm9VRncKZS9HZ0hpamNBY1l0TlJYektzb2VhSUR2OHNUdkRuMndzTGkxcHdRVnR3UEVSVnZTQjdiVkU4dGN6SGZSNDZsagp0enFObGZyQkQzZW0vbHl4V1JvTTQ4czhxVTVNa1ZETklramtpZzc4VVFLQmdRRDdvTC9YS3R0Q1FsRUlocDNtCnFzMUpPekJxcE1Fb3BST3BvWURMMURUZ3NYWlNyVlp4L2lTSWY4WnBNTlpEeDdQcWFxcTgxOTE0emNFZElnekEKWkVwVHVLcGQ1bHhkNzZLYzFaVjhVZjBjYUlWbmFkQ2tDNWczQXlKNHk4VHdjdmppWUdyY3NPWDhVU1hiOGpnUQo4S1Q2QkdTVTc0SFN3VDFIR0hJalFDeHBVd0tCZ1FEVHdrWFZzdDE1Y3JHQWI1ZS9UTmR6MGQvVGlrQ25ocWpICm80bVlncDI5TlVsdEN5MFZOTGhXTFlZVjh6ZUYxYXhtdFpnT0pFQTN3Unc0VmQ4QVpCZGZSQW9Cd2ZjZlVIamgKYW5OVWxXdm5XZjZJRVc3NzVYeERQNkdtOGpCQXlMUVhFd2dpWCs0Tk1QTDM2ZXphYTJ5bElIYzRsUDc4am5KagpxZkk2a3NZSkZRS0JnRXR1THRRVGx0TFFDbmFoMUNmWHY5NWFEZk9LSEJWUkZ3bmN6ajFNQ2VYcGpPelA1WUFhCmpWMFY0S2FiNno4NldHYkhQeE9KS20wU1VQZW93MlhSS3E3YVJzZ0xURmtrZ3Z5ODBpa0ljdlhYSjFhTzArcTUKUnhJR3NJakJuUEh2cFVoSFd3RjVUaGhMUXl3aCtraXB1dXJ2OGk3cmRXRjJhQ1l0MzlsTlhZTGRBb0dCQUlzcwp0dnRCcUlCR21sVEFneXFPMVZmZ3kwdmNKS3cyTzcyaVJTL0FRTzMzRk1BZlJVMFhya090ZmQvMVR6dWQrTVkwCmViQnBzTzh6ODFrdlR2YVIwaTZocURZSmhtTEZYLzAvR25ld0VSQW52THN2UWhNNmU1WXpQd3BiU00xN1c2bUMKcjZqd0JhUVQxTXlOcVViUXJjSkZlVFh0N3p5TVhyQVVKUWpNS0c0VkFvR0FmNzN1VHBrNmFOYnh1SjEzc2ZxWQpCNjhQMmFHektzMEVZOS83cmJWRCthZXQ0RWNiVFhFd3pNQ255WDM5enl2QkJxWG9JbkZxUlMvZDlLZlRZOEE4CmxtS0hJTGZuM2pqeWMrMEM1S2RvTy9KUktxR2pWajEvVUhzT2xSMUFJTW5CQVpiZVV4WCtrOHhHamVHRjdyL0oKWktQTnZUZjd4VXlrMi9UV3pYVnFZREE9Ci0tLS0tRU5EIFBSSVZBVEUgS0VZLS0tLS0K

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
      secretName: tls-secret  
  rules:  # 可以定义多个路由规则,Service的type为ClusterIP即可(NodePort也行)
    - host: nginx.local.com  # 通过该域名访问nginx,可以在本地机/etc/hosts文件添加 ingress所在集群节点ip nginx.local.com 模拟
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
  ownerReferences: # 该对象所依赖的对象列表,一般由k8s自动生成,如果列表中的所有对象都被删除后,该对象将被垃圾回收
    - apiVersion: 
      kind: # 如果该Pod是由Deployment对象的Pod模板产生,则值为ReplicaSet,name值为ReplicaSet对应名字
      name: 
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
      image: redis:alpine  # 同一个Pod中如果两个容器运行的程序使用相同端口,则会启动失败,说明端口也是共享的
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
          host: # 默认是pod ip 
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
#      emptyDir:
#        sizeLimit: 500Mi
#      hostPath:
#        path: /home/docker
#        type: DirectoryOrCreate  # 目录不存在就先创建再使用,存在则直接使用,还支持Directory|File|FileOrCreate
#      nfs: 
#        server: 192.168.2.2 # nfs服务器地址
#        path: /data # 共享文件路径
  
  nodeName:  # 将Pod调度到指定的Node节点上
  nodeSelector: # 将Pod调度到标签ssd=true的节点上
#    ssd: "true"
  restartPolicy: Always # Always容器失效时重启(默认),OnFailure容器终止运行且退出码不为0时重启,Never不重启容器,每个容器重启间隔阶梯形增长

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

### mysql部署
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




