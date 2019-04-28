from random import random
from operator import add
from pyspark.sql import SparkSession
from pyspark.sql import functions as f

def count_pi(spark):
    def f(_):
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
    # counts = rdd.flatMap(lambda x: x.split(' ')).map(lambda x: (x, 1)).reduceByKey(add)  # rdd类型,reduceByKey对key相同的数据集,都使用指定的函数聚合到一起
    # for word,count in counts.collect():
    #     print(word,count)

    df=spark.read.text("resources/people.txt") 
    # new_df=df.withColumn('word', f.explode(f.split(df['value'], ' '))).groupBy('word').count().sort('count',ascending=False)
    new_df=df.select(f.explode(f.split(df['value'],' ')).alias('word')).groupBy('word').count().sort('count',ascending=False)
    new_df.show()
    
def sort(spark):
    rdd = spark.sparkContext.textFile("resources/sort.txt")  # sort.txt格式必须满足要求
    sortedCount = rdd.flatMap(lambda x: x.split(' ')).map(lambda x:int(x)).sortBy(ascending=False,keyfunc=lambda x:x)
    for num in sortedCount.collect():
        print(num)

if __name__ == "__main__":
    spark = SparkSession.builder.appName("common").getOrCreate() # 交互式命令行中的spark
    # count_pi(spark)
    word_count(spark)
    # sort(spark)
    spark.stop()

