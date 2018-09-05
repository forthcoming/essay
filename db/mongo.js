/**************************************************************************
basic
collection => table
document => row
***************************************************************************/
show dbs;
show profile;  // print the five most recent operations that took 1 millisecond or more.
show collections;
use dbname;  切换库(不存在则创建)
db.user.drop();
db.dropDatabase();
db.user.renameCollection("detail");
db.user.findOne()._id.getTimestamp();

/**************************************************************************
_id
mongodb默认按_id升序输出,so最先插入的数据会靠前展示
***************************************************************************/
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import os

client=MongoClient('mongodb://192.168.105.20:27017')
db=client['Atlas']
test=db['test']

_id=str(test.find_one()['_id']) # 12字节,是一个由24个16进制数字组成的字符串
timestemp=_id[:8]               # 时间戳
machine_id=_id[8:14]            # machine identifier,通常是机器主机名的散列值,这样能确保不同主机生成不同的ObjectId.
pid=_id[14:18]                  # PID,来自产生ObjectId的进程的进程标识符,为了确保在同一台机器上并发的多个进程产生的ObjectId是唯一的.
counter=_id[18:24]              # 自动增加的计数器,确保相同进程的同一秒产生的ID也是不同的.
print(int(pid,16)==os.getpid()) # True

start = ObjectId.from_datetime(generation_time=datetime.strptime('1992-08-24 12:34:56',"%Y-%m-%d %H:%M:%S"))
x=test.find_one()['_id'].generation_time
print(x,type(x))  # 2018-08-10 03:22:56+00:00 <class 'datetime.datetime'>

client.close()

/**************************************************************************
CRUD
***************************************************************************/
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
db.user.updateOne({},{$rename:{old:"new"}});  // 重命名字段,the update operation document must contain atomic operators
db.user.updateMany({},{$inc:{age:10}}});  // the update operation document must contain atomic operators,eg. $set
db.user.updateMany({},{$mul:{price:100}});  // price都乘100
db.user.updateMany({},{$unset:{color:""}});   // 删除某个字段
db.user.updateMany({name:'avatar'},{$set:{name:'wangwu'}});
db.user.updateMany({slug: 'avatar'},{$set: { item: 2 },$setOnInsert: {slug:'akatsuki',age:333}},{upsert:true});
/*
没找到则将set,inc,setOnInsert等所有关键词内容合并到查询条件中,然后一并插入,依赖于upsert=true
找到则忽略掉setOnInsert,将其他关键词内容合并到查询条件中，然后一并插入
*/

/**************************************************************************
index
相同索引只创建一次
sort要跟索引完全保持一致,sort多个字段就要建立复合索引,这要求字段个数,顺序完全一致,注意asc和desc必须跟索引完全一致或完全相反,否则索引会失效
find使用索引情况比较复杂，建议通过explain观察
If MongoDB cannot use an index to get documents in the requested sort order, the combined size of all documents in the sort operation, plus a small overhead, must be less than 32 megabytes.
***************************************************************************/
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
hashed:哈希索引,支持"=,in"查询,但不支持范围查询,不能创建具有哈希索引字段的复合索引或在哈希索引上指定唯一约束;
但可以在同一个字段上创建哈希索引和非哈希索引,MongoDB将对范围查询使用标量索引
*/

db.restaurants.createIndex({cuisine:1},{partialFilterExpression:{rating:{$gt:5}}});
/*
部分索引:仅索引符合过滤器表达式的文档,索引存储占用空间更少,创建和维护成本更低。
To use the partial index,a query must contain the filter expression (or a modified filter expression that specifies a subset of the filter expression) as part of its query condition.
*/

db.contacts.createIndex({name:1},{partialFilterExpression:{name:{$exists:true}}});
/*
the same behavior as a sparse index,建议用部分索引替代稀疏索引,普通索引会把不存在的field列认为null并建立索引
*/

// 以下查询可以使用部分索引,因为查询谓词{$gte:8}是过滤器表达式{$gt:5}的子集
db.restaurants.find( { cuisine: "Italian", rating: { $gte: 8 } } )；
// 以下查询不能使用部分索引
db.restaurants.find( { cuisine: "Italian", rating: { $lt: 8 } } );
db.restaurants.find( { cuisine: "Italian" } );

/**************************************************************************
geo
***************************************************************************/
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

/**************************************************************************
cursor
***************************************************************************/
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
        
/**************************************************************************
aggregate
***************************************************************************/       
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

/**************************************************************************
example
***************************************************************************/
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
