from random import random
from operator import add
from pyspark.sql import SparkSession,functions as F

def count_pi(spark):
    def f(_): # rdd中的udf不需要像dataframe那样注册
        x, y = random(), random()
        return x*x + y*y < 1
    num_samples=200000
    sc = spark.sparkContext  # 交互式命令行中的sc
    rdd = sc.parallelize([1]*num_samples, 2)
    # count = rdd.map(f).reduce(add)
    # count = rdd.filter(f).reduce(add)   # 由于这里rdd的每一行都是1,所以这里可以用reduce
    count = rdd.filter(f).count()
    print(f"Pi is roughly {4.0 * count / num_samples}")

def word_count(spark):
    # rdd = spark.sparkContext.textFile("resources/people.txt")
    # counts = rdd.flatMap(lambda x: x.split(' ')).map(lambda x: (x, 1)).reduceByKey(add)  
    # print(counts.collect())
    '''
    counts是rdd类型,reduceByKey对key相同的数据集,都使用指定的函数聚合到一起
    add这里相当于"lambda x,y:x+y",注意自己定义聚合函数的格式
    reduceByKey相当于dataframe里面的groupBy
    '''

    df=spark.read.text("resources/people.txt") 
    # new_df=df.withColumn('word', F.explode(F.split(df['value'], ' '))).groupBy('word').count().sort('count',ascending=False)
    new_df=df.select(F.explode(F.split(df['value'],r'\s+')).alias('word')).groupBy('word').count().sort('count',ascending=False)
    new_df.show()

def sort(spark):
    rdd = spark.sparkContext.textFile("resources/sort.txt")  # sort.txt格式必须满足要求
    sortedCount = rdd.flatMap(lambda x: x.split(' ')).map(lambda x:int(x)).sortBy(ascending=False,keyfunc=lambda x:x)
    for num in sortedCount.collect(): # collect返回list类型
        print(num)

if __name__ == "__main__":
    spark = SparkSession.builder.appName("common").getOrCreate() # 交互式命令行中的spark
    # count_pi(spark)
    word_count(spark)
    # sort(spark)
    spark.stop()

