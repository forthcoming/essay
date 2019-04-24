from random import random
from operator import add
from pyspark.sql import SparkSession


def count_pi(spark):
    def f(_):
        x, y = random(), random()
        return x*x + y*y < 1
    num_samples=200000
    sc = spark.sparkContext  # 交互式命令行中的sc
    rdd = sc.parallelize(range(0, num_samples), 2)
    count = rdd.map(f).reduce(add)
    # count = rdd.filter(f).count()
    print(f"Pi is roughly {4.0 * count / num_samples}")

def word_count(spark):
    rdd = spark.sparkContext.textFile("resources/people.txt")
    counts = rdd.flatMap(lambda x: x.split(' ')).map(lambda x: (x, 1)).reduceByKey(add)  # rdd类型
    for word,count in counts.collect():
        print(word,count)

def sort(spark):
    rdd = spark.sparkContext.textFile("resources/sort.txt")  # sort.txt格式必须满足要求
    sortedCount = rdd.flatMap(lambda x: x.split(' ')).map(lambda x: (int(x), 1)).sortByKey()
    for num, unitcount in sortedCount.collect():
        print(num,unitcount)


if __name__ == "__main__":
    spark = SparkSession.builder.appName("common").getOrCreate() # 交互式命令行中的spark
    # count_pi(spark)
    # word_count(spark)
    sort(spark)
    spark.stop()

