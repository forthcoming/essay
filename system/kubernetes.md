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
minikube start -n 3 --image-mirror-country='cn'  # -n指定集群节点个数
minikube dashboard  # 查看控制面板
minikube status
minikube stop
minikube delete # 删除本地的k8s集群
minikube ssh -n minikube # 登录节点,-n要ssh访问的节点，默认为主控制平面(建议修改docker镜像源,否则kubectl run无法拉取镜像)
minikube cp file node_name:path  # 将本地机文件拷贝到指定节点目录

kubectl api-versions # 查看所有的对象版本号
kubectl api-resources # 查看所有的对象
kubectl explain pod # 查看对象字段的yaml文档
kubectl get node  # 查看节点信息
kubectl exec pod_name -c container_name -it -- /bin/sh  # 进入Pod指定容器内部执行命令
kubectl cp file pod_name:pod_path  # 将主机文件拷贝到pod指定目录

kubectl create ns dev # 创建名为dev的命名空间
kubectl delete ns dev  # 删除命名空间dev及其下所有pod
kubectl run nginx --image=nginx:alpine -n dev # 在dev(默认为default)命名空间下运行名为nginx的pod,k8s会自动拉取并运行
kubectl get pod -o wide [--v=9] # 查看pod,-o显示详细信息,--v=9会显示详细的http请求
kubectl describe pod nginx -n dev # pod相关描述,通过最后的Events描述可以看到pod构建的各个细节
kubectl delete pod --all --force  # 强制删除所有pod
kubectl logs -f pod_name -c container_name # 查看pod运行日志

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: dev

---

apiVersion: apps/v1
kind: Deployment
metadata:
  name: deploy-nginx
  namespace: dev
spec:
  replicas: 3
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

apiVersion: v1
kind: Pod
metadata:
  name: apps
  namespace: dev
  labels:
    version: "3.0"
    env: test
spec:
  containers:
    - name: python-container
      image: python:alpine
      imagePullPolicy: Always # Always用远程,Never用本地(不是节点本地),IfNotPresent优先用本地再远程
      command: ["/bin/sh"] # 如果在配置文件中设置了容器启动时要执行的命令及其参数,容器镜像中自带的命令与参数将会被覆盖而不再执行
      args: ["-c", "while true; do echo hello; sleep 5;done"] # 如果配置文件中只是设置了参数,却没有设置其对应的命令,那么容器镜像中自带的命令会使用该新参数作为其执行时的参数
      env: # 容器环境变量列表 
      resources:
        limits: # 限制容器运行时最大占用资源,当资源超过最大限制时会重启
          cpu: 2 # 最多2核
          memory: "10Gi" # 最大内存
        requests: # 设置容器需要的最小资源, 低于限制容器将无法启动
          cpu: 1
          memory: "10Mi"
    - name: redis-container
      image: redis:alpine
  nodeName:  # 将Pod调度到指定的Node节点上,还可以根据nodeSelector指定节点
  restartPolicy: Always # Always容器失效时重启(默认),OnFailure容器终止运行且退出码不为0时重启, Never不重启容器,每个容器重启间隔阶梯形增长
```
kubectl apply -f nginx.yaml  # 创建或更新
kubectl delete -f nginx.yaml

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

Label用于给某个对象定义标识,Label Selector用于查询和筛选拥有某些标签的资源,可以使用多个组合查询
基于等式的Label Selector: 
name=avatar选择所有Label中key=name且value=avatar的对象; name!=avatar选择所有Label中key=name且value!=avatar的对象
基于集合的Label Selector: 
name in (v1,v2)选择所有Label中key=name且value=v1或value=v2的对象; name not in (v1,v2)选择所有Label中key=name且value!=v1且value!=v2的对象
kubectl get pod -l "version=3.0" -n dev # 查询指定标签的pod

Service可以看做一组同类Pod对外的访问接口,应用可以方便的实现服务发现和负载均衡

YAML是JSON的超集,支持整数、浮点数、布尔、字符串、数组和对象等数据类型,大小写敏感,任何合法的JSON文档也都是YAML文档
使用空白与缩进表示层次
使用 # 书写注释
使用 - 开头表示数组
使用 : 表示对象,格式与JSON基本相同,但Key不需要双引号
使用 --- 在一个文件里分隔多个YAML对象
表示对象的 : 和表示数组的 - 后面都必须有空格
