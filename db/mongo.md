```
https://api.mongodb.com/python/current/faq.html
PyMongo is thread-safe and provides built-in connection pooling for threaded applications.But it's not fork-safe.
经验: 带有连接池的对象都是线程安全,非进程安全
collection => table
document => row
mongodb默认按_id升序输出,so最先插入的数据会靠前展示
```

### mongo监控

```
mongostat -h 10.1.140.179:27017
导出数据
mongoexport -h rds.aliyuncs.com:3717 -u name -p M7webU -d Atlas -c category -o category.json --authenticationDatabase admin
导入数据
mongoimport -h 192.168.105.20:27017 -d Atlas -c category category.json
mongodump -h IP --port 端口 -u 用户名 -p 密码 -d 数据库 -c 表 -o 文件存放路径
-h 指明数据库宿主机的IP
--port 指明数据库的端口 
-u 指明数据库的用户名
-p 指明数据库的密码
-d 指明数据库的名字
-c 指明collection的名字
-o 指明到要导出的文件名
-q 指明导出数据的过滤条件
```

```javascript
show dbs;
show profile;  // print the five most recent operations that took 1 millisecond or more.
show collections;
use dbname;  切换库(不存在则创建)
db.user.drop();
db.dropDatabase();
db.user.renameCollection("detail");
db.user.findOne()._id.getTimestamp();
```

```python
import os
from datetime import datetime

from bson import ObjectId
from pymongo import MongoClient

# timeoutMS: 控制驱动程序在执行操作时将等待多长时间
# connectTimeoutMS: 如果与数据库请求建立连接的时间超过ConnectionTimeOut,就会抛ConnectionTimeOutException
# socketTimeoutMS: 如果数据库处理数据用时过长,超过了SocketTimeOut,就会抛出SocketTimeOutExceptin,即服务器响应超时,服务器没有在规定的时间内返回给客户端数据
client = MongoClient(
    host='mongodb://username:password@10.73.20.11:27017,10.73.20.10:27017/admin?authSource=admin',
    socketTimeoutMS=10000,
    connectTimeoutMS=10000,
    connect=False,
)
db = client['Atlas']
test = db['test']

_id = str(test.find_one()['_id'])  # 12字节,是一个由24个16进制数字组成的字符串
timestemp = _id[:8]  # 时间戳
machine_id = _id[8:14]  # machine identifier,通常是机器主机名的散列值,这样能确保不同主机生成不同的ObjectId.
pid = _id[14:18]  # PID,来自产生ObjectId的进程的进程标识符,为了确保在同一台机器上并发的多个进程产生的ObjectId是唯一的.
counter = _id[18:24]  # 自动增加的计数器,确保相同进程的同一秒产生的ID也是不同的.
print(int(pid, 16) == os.getpid())  # True

start = ObjectId.from_datetime(generation_time=datetime.strptime('1992-08-24 12:34:56', "%Y-%m-%d %H:%M:%S"))
x = test.find_one()['_id'].generation_time
print(x, type(x))  # 2018-08-10 03:22:56+00:00 <class 'datetime.datetime'>
client.close()
```

### CRUD

```javascript
db.user.distinct(field,{depth:'A'});   // 查询depth为A的所有不重复field
db.user.find({b:null});  // b不存在或者b=null,pymongo用None表示
db.user.find({b:{$exists:false}});  // b不存在
db.user.find(it=>it.platform==='cuckoo');
db.user.find({"category":/electronics/i});  // 查找字符串包含electronics的记录，不区分大小写
db.user.find({name:'avatar'});
db.user.find({key:{ $ne:'TV'}});
db.user.find({'platform':'1688','price': { '$elemMatch': { 'cheep': {'$type':'double'}}}},{'_id':1,'price':1});
db.user.find({error: { $exists: true }});
db.user.find({name:'avatar'}).count();
db.user.find({name:'avatar'}).skip(2).limit(3);
db.user.find({name:'avatar'},{name:1,_id:0});
db.user.find({$and:[{sellers:{$gt:5}},{sellers:{$lt:10}}]});
db.user.find({$or:[{_id:"B01AVSDXQI"},{price:12}]});
db.getCollection("user").find({category:{$in:['phone','watch']}});
db.user.findOneAndDelete({name:'office'});  // Finds a single document and deletes it, returning the document.
db.user.findOneAndReplace({name:'office'},{score:5});
/*
Finds a single document and replaces it, returning either the original or the replaced document.
findOneAndReplace method differs from findOneAndUpdate by replacing the document matched by filter, rather than modifying the existing document.
the replace operation document must not contain atomic operators
*/
db.user.findOneAndUpdate({name:'office'},{score:5});
/*
Finds a single document and updates it, returning either the original or the updated document.
the update operation document must contain atomic operators
*/
db.user.insertOne({name:'avatar',age:22});  // 向collection插入数据(不存在则创建)，且自动加上主键_id
db.user.insertMany([{a:1},{b:2}])
db.user.deleteOne({name:'avatar'});  
db.user.deleteMany({name:'avatar'});
db.user.updateOne({},{$rename:{old:"new"}}); // 重命名字段,the update operation document must contain atomic operators
db.user.updateMany({},{$inc:{age:10}}});     // the update operation document must contain atomic operators,eg. $set
db.user.updateMany({},{$mul:{price:100}});   // price都乘100
db.user.updateMany({},{$unset:{color:""}});  // 删除某个字段
db.user.updateMany({name:'avatar'},{$set:{name:'wangwu'}});
db.user.updateMany({slug: 'avatar'},{$set: { item: 2 },$setOnInsert: {slug:'akatsuki',age:333}},{upsert:true});
/*
没找到则将set,inc,setOnInsert等所有关键词内容合并到查询条件中,然后一并插入,依赖于upsert=true
找到则忽略掉setOnInsert,将其他关键词内容合并到查询条件中,然后一并插入
*/
```

### index

```javascript
相同索引只创建一次
sort要跟索引完全保持一致,sort多个字段就要建立复合索引,这要求字段个数,顺序完全一致,注意asc和desc必须跟索引完全一致或完全相反,否则索引会失效
sort按某个字段-1排序时,不存在or等于null的会被放到最后
If MongoDB cannot use an index to get documents in the requested sort order, the combined size of all documents in the sort operation, 
plus a small overhead, must be less than 32 megabytes.

db.collection.getIndexes();
db.collection.dropIndexes();
db.collection.dropIndex(field);

db.collection.find({field:value}).explain();  
/*
winningPlan下面indexBounds当前查询使用的索引
By default, cursor.explain() runs in queryPlanner verbosity mode.
MongoDB runs the query optimizer to choose the winning plan for the operation under evaluation. 
*/

db.collection.createIndex({field:1},{unique:true,background:true});  
/*
background:后台创建索引,代价是创建时间变长
unique:唯一索引,前提是field列不相等,插入不合要求的field列会出错
*/

db.collection.createIndex({field1:1,field2:-1 });  // 复合索引

db.collection.createIndex({ field:"hashed" });
/*
hashed:哈希索引,支持"=,in"查询,但不支持范围查询,不能创建具有哈希索引字段的复合索引或在哈希索引上指定唯一约束
但可以在同一个字段上创建哈希索引和非哈希索引,MongoDB将对范围查询使用标量索引
*/

db.restaurants.createIndex({cuisine:1},{partialFilterExpression:{rating:{$gt:5}}});
/*
部分索引:仅索引符合过滤器表达式的文档,索引存储占用空间更少,创建和维护成本更低
To use the partial index,a query must contain the filter expression (or a modified filter expression that specifies a subset of the filter expression) as part of its query condition.
*/

db.contacts.createIndex({name:1},{partialFilterExpression:{name:{$exists:true}}});
/*
the same behavior as a sparse index,建议用部分索引替代稀疏索引,普通索引会把不存在的field列认为null并建立索引
*/

// 以下查询可以使用部分索引,因为查询谓词{$gte:8}是过滤器表达式{$gt:5}的子集
db.restaurants.find( { cuisine: "Italian", rating: { $gte: 8 } } );
// 以下查询不能使用部分索引
db.restaurants.find( { cuisine: "Italian", rating: { $lt: 8 } } );
db.restaurants.find( { cuisine: "Italian" } );
```

### geo

```javascript
db.places.insertMany([
    {
        loc : { type: "Point", coordinates: [ -73.97, 40.77 ] },
        name: "Central Park",
        category : "Parks"
    },
    {
        loc : { type: "Point", coordinates: [ -73.88, 40.78 ] },
        name: "La Guardia Airport",
        category : "Airport"
    }
]);
// 2d:非球面索引(如游戏地图)  2dsphere:球面索引
db.places.createIndex({loc:'2dsphere'});  // 需要被间索引的字段(这里是loc),其中的子对象是由GeoJson指定,字段如type,coordinates都不能随意更改
db.places.find( //前提是被查询字段已经建立2dsphere索引,returns whose location is at least 1000 meters from and at most 5000 meters from the specified point, ordered from nearest to farthest
   {
     loc: {
        $nearSphere: { 
           $geometry: {
              type : "Point",
              coordinates : [ -73.9667, 40.78 ]
           },
           $minDistance: 1000,
           $maxDistance: 5000
        }
     }
   }
);
```

### cursor

```javascript
var name='user';
var cursor=db[name].find({age:{$exists: true}});
while (cursor.hasNext()) {
    var id=cursor.next();
    delete id.age;
    id.flag=Boolean(id.flag);
    db[name].replaceOne({_id:id['_id']},id);
}

from pymongo import MongoClient,ASCENDING
client=MongoClient('mongodb://192.168.105.20:27017')
user=client['Atlas']['user']
done = False
skip = 0
while not done:  # 防止游标超时
    cursor = user.find()
    cursor.sort('_id',ASCENDING) # recommended to use time or other sequential parameter.
    cursor.skip(skip)
    try:
        for doc in cursor:
            skip += 1
            # do_something()
        done = True
    except Exception as e:
        print(e)
```

### aggregate

```javascript
db.user.aggregate([
    {
        $match:{error:"BLACKLIST"}
    },
    {
        $group: {
            _id:{b_id:"$b_id",c_id:"$c_id"},  // _id意思是按后面给的字段分组,_id:null意思是不分组
            cnt:{$sum: 1}, 
            num:{$sum:'$sales'}
        }
    },
    {
        $match:{num:{$gte:3}}                // 第二个$match相当于SQL中的having
    }  
]);

db.galance.aggregate([
    {
        $lookup:{              // left join,匹配不到detail时cmp为[]
            from: "detail",
            localField: "_id",
            foreignField: "_id",
            as: "cmp"
        }
    },
    {
        $match:{
            category:{$exists: true},
            cmp:{$ne:[]}
        }
    },
    {
        $project:{
            _id:0,
            category_url:0,
            category_name:0,
            parent_id:0,
            'cmp._id':0,
            'cmp.category_url':0,
            'cmp.category_name':0,
            'cmp.parent_id':0,
            'cmp.dw_web_id':0
        }
    }
]);

db.user.aggregate([   // 去重
    {
        $group:{_id:{name:'$name'},count:{$sum:1},dups:{$addToSet:'$_id'}}  // $addToSet将聚合的数据id放入到dups数组
    },
    {
        $match:{count:{$gt:1}}  // 过滤没有重复的数据
    }
]).forEach(function(item){
    item.dups.shift();  // 剔除数组中第一条_id,避免删掉所有的数据
    db.user.deleteMany({_id: {$in: item.dups}});
});

// { "_id" : 1, "item" : "ABC1", sizes: [ "S", "M", "L"] }
db.inventory.aggregate( [ { $unwind : "$sizes" } ] )
/*
{ "_id" : 1, "item" : "ABC1", "sizes" : "S" }
{ "_id" : 1, "item" : "ABC1", "sizes" : "M" }
{ "_id" : 1, "item" : "ABC1", "sizes" : "L" }
*/
```

### example

```javascript
use Atlas;  // shell中需要

var name_en=[
    "cloth",
    "shoes",
    "sports"
];
var platforms=[
    'cuckoo',
    '1688'
];

for(let name of name_en){
    for(let platform of platforms){
        var cursor=db.getCollection(`image_phash_${name}_${platform}`).find({phash:{$in:['8000000000000000','b36acc9516eec1c1']}},{system_id:1,_id:0});
        while(cursor.hasNext()){
            var system_id=cursor.next()['system_id'];
            print(system_id);                        
            var node=db.getCollection(`cluster_node_${name}`);   // 必须使用getCollection
            var result=node.findOne({'system_id':system_id},{cluster_id:1,_id:0});
            var cluster_id=0;
            if(result){
                cluster_id=result['cluster_id'];
            }
            node.deleteOne({'system_id':system_id});
            if(node.findOne({'cluster_id':cluster_id,'on_sale':true})){
                var data=node.find({'cluster_id':cluster_id,'on_sale':true},{'serial_num':1,'_id':0}).sort({'serial_num':1}).limit(1);
                node.updateMany({'cluster_id':cluster_id},{$set:{'cluster_id':data.next()['serial_num']}},{multi:true});
            }
            db.getCollection(`cluster_edge_${name}`).deleteMany({$or:[{"from_node_id":system_id},{"to_node_id":system_id}]});
            db.getCollection(`image_phash_${name}_${platform}`).deleteOne({'system_id':system_id});
        }
    }
}
```

### MapReduce(支持分布式操作)

```javascript
db.user.mapReduce(
    function(){  // map
        // for(var idx=0;idx<this._id.length;++idx){
            var key={id:this.id,name:this.name};
            var value={
                count:1,
                score:this.score,
            };
            emit(key,value);
        // }
    },
    function(key,values){  // reduce
        var reducedVal={count:0,score:0};
        for(let value of values){
            reducedVal.count+=value.count;  // 注意count计算方式
            reducedVal.score+=value.score;
        }
        return reducedVal
    },
    {
        out:{inline:1}, 
        // out: {merge: 'results'},
        query:{id:{$ne:2}},
        finalize:function (key, reducedVal) {  // 计算平均数等操作只能放在此处执行
            reducedVal.avg = reducedVal.score/reducedVal.count;
            return reducedVal;
        }
    }
).find()

/*
map:
The map function is responsible for transforming each input document into zero or more documents. It can access the variables defined in the scope parameter
In the map function, reference the current document as this within the function
The map function should not access the database for any reason.
The map function may optionally call emit(key,value) any number of times to create an output document associating key with value.


reduce:
The reduce function should not access the database, even to perform read operations.
The reduce function should not affect the outside system.
MongoDB will not call the reduce function for a key that has only a single value. The values argument is an array whose elements are the value objects that are “mapped” to the key.
MongoDB can invoke the reduce function more than once for the same key. In this case, the previous output from the reduce function for that key will become one of the input values to the next reduce function invocation for that key.
The reduce function can access the variables defined in the scope parameter.
The inputs to reduce must not be larger than half of MongoDB’s maximum BSON document size. This requirement may be violated when large documents are returned and then joined together in subsequent reduce steps.


Because it is possible to invoke the reduce function more than once for the same key, the following properties need to be true:
the type of the return object must be identical to the type of the value emitted by the map function.


the reduce function must be associative. The following statement must be true:
reduce(key, [ C, reduce(key, [ A, B ]) ] ) == reduce( key, [ C, A, B ] )


the reduce function must be idempotent. Ensure that the following statement is true:
reduce( key, [ reduce(key, valuesArray) ] ) == reduce( key, valuesArray )


the reduce function should be commutative: that is, the order of the elements in the valuesArray should not affect the output of the reduce function, so that the following statement is true:
reduce( key, [ A, B ] ) == reduce( key, [ B, A ] )


query:
Specifies the selection criteria using query operators for determining the documents input to the map function


out:
out: { <action>: <collectionName> [, db: <dbName>] }
<action>: Specify one of the following actions:
replace
Replace the contents of the <collectionName> if the collection with the <collectionName> exists.
merge
Merge the new result with the existing result if the output collection already exists. If an existing document has the same key as the new result, overwrite that existing document.
reduce
Merge the new result with the existing result if the output collection already exists.
If an existing document has the same key as the new result, apply the reduce function to both the new and the existing documents and overwrite the existing document with the result.
db
Optional. The name of the database that you want the map-reduce operation to write its output. By default this will be the same database as the input collection.

sort:
Sorts the input documents. This option is useful for optimization. For example, specify the sort key to be the same as the emit key so that there are fewer reduce operations.
The sort key must be in an existing index for this collection.

limit:
Specifies a maximum number of documents for the input into the map function.

scope:
Specifies global variables that are accessible in the map, reduce and finalize functions.

finalize:
The finalize function receives as its arguments a key value and the reducedValue from the reduce function. Be aware that:
The finalize function should not access the database for any reason.
The finalize function should be pure, or have no impact outside of the function (i.e. side effects.)
The finalize function can access the variables defined in the scope parameter.
*/


db.image_match_result_jewellery.mapReduce(
    function(){
        if(this.b_id>this.c_id){
            [this.b_id,this.c_id]=[this.c_id,this.b_id];
        }
        var key={b_id:this.b_id,c_id:this.c_id};
        var value={
            match_num:1,
            hash_diff:this.hash_diff,
            b_id:this.b_id,
            c_id:this.c_id
        };
        emit(key,value);
    },
    function(key,values){
        var reducedVal={
            match_num:0,
            hash_diff:Number.POSITIVE_INFINITY,
            b_id:values[0].b_id,
            c_id:values[0].c_id
        };
        for(let value of values){
            reducedVal.match_num+=value.match_num;
            if(reducedVal.hash_diff>value.hash_diff){
                reducedVal.hash_diff=value.hash_diff
            }
        }
        return reducedVal
    },
    {
        out: {reduce: 'results',nonAtomic:false},
        scope:{
            date:(function(){
                var convert=s=>s < 10 ? '0' + s : s;
                var myDate = new Date();
                var year = myDate.getFullYear();
                var month = myDate.getMonth() + 1;
                var date = myDate.getDate();
                var h = myDate.getHours();
                var m = myDate.getMinutes();
                var s = myDate.getSeconds();
                return `${year}-${convert(month)}-${convert(date)} ${h}:${convert(m)}:${convert(s)}`;
            })(),  // 只会执行一次
        },
        query:{'$or':[{'added_to_item_match':{'$exists':false}},{'added_to_item_match':false}]},
        sort:{b_id:1,c_id:-1},
        finalize:function (key, reducedVal) {
            reducedVal.sim_score = reducedVal.hash_diff/reducedVal.match_num;
            reducedVal.date=this.date;
            return reducedVal;
        }
    }
)
```

```python
from datetime import datetime

from bson.code import Code
from bson.son import SON
from pymongo import MongoClient

client = MongoClient('mongodb://192.168.105.20:27017')
db = client['Atlas']
image_match = db['image_match_result_jewellery']

mapper = Code('''
    function(){
        if(this.b_id>this.c_id){
            [this.b_id,this.c_id]=[this.c_id,this.b_id];
        }
        var key={b_id:this.b_id,c_id:this.c_id};
        var value={
            match_num:1,
            hash_diff:this.hash_diff,
            b_id:this.b_id,
            c_id:this.c_id,
            b_url:this.b_url,
            c_url:this.c_url
        };
        emit(key,value);
    }
''')

reducer = Code('''
    function(key,values){
        var reducedVal={
            match_num:0,
            hash_diff:Number.POSITIVE_INFINITY,
            b_id:values[0].b_id,
            c_id:values[0].c_id,
        };
        for(let value of values){
            reducedVal.match_num+=value.match_num;
            if(reducedVal.hash_diff>value.hash_diff){
                reducedVal.hash_diff=value.hash_diff;               
                reducedVal.hash_diff=value.hash_diff;
                reducedVal.hash_diff=value.hash_diff;
            }
        }
        return reducedVal
    }
''')

finalize = Code('''
    function(key, reducedVal) {
        reducedVal.sim_score = reducedVal.hash_diff/reducedVal.match_num;
        reducedVal.updated_at=this.updated_at;
        return reducedVal;
    }
''')

result = image_match.map_reduce(
    mapper,
    reducer,
    out=SON([("reduce", "results"), ("db", 'Atlas')]),
    query={'$or': [{'added_to_item_match': {'$exists': False}}, {'added_to_item_match': False}]},
    # perform incremental Map-Reduce
    sort=SON([('b_id', -1), ('c_id', 1)]),
    finalize=finalize,
    scope={'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')},  # 只执行一次
    limit=500000,
    full_response=True,
)
print(result)
client.close()

# During the operation, map-reduce takes the following locks:
# The read phase takes a read lock. It yields every 100 documents.
# The insert into the temporary collection takes a write lock for a single write.
# If the output collection does not exist, the creation of the output collection takes a write lock.
# If the output collection exists, then the output actions (i.e. merge, replace, reduce) take a write lock. This write lock is global, and blocks all operations on the mongod instance.
# NOTE
# The final write lock during post-processing makes the results appear atomically. However, output actions merge and reduce may take minutes to process.
# For the merge and reduce, the nonAtomic flag is available, which releases the lock between writing each output document. See the db.collection.mapReduce() reference for more information.
```