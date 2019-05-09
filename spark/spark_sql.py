from pyspark.sql import SparkSession,Row,functions as F
from pyspark.sql.types import *

def basic_df(spark):
    # host='localhost'
    # port=3306
    # db='test'
    # user='root'
    # pwd='root'
    # pushdown_query = "(select * from employee limit 10) tmp"
    # jdbc_url = f"jdbc:mysql://{host}:{port}/{db}?user={user}&password={pwd}"
    # df = spark.read.jdbc(url=jdbc_url, table=pushdown_query)
    # df.show()
    # df.write.jdbc(url=jdbc_url, table='teacher',mode='append')

    data = [
        ("2015-05-14 03:53:00", "WARRANT ARREST"),
        ("2015-05-14 03:53:00", "TRAFFIC VIOLATION"),
        ("2015-05-14 03:33:00", "TRAFFIC VIOLATION")
    ]
    df = spark.createDataFrame(data, ["date", "desc"])
    df = df.withColumn('wordCount', F.size(F.split(df['desc'], ' ')))
    df.show(10)  # show first 10 lines
    # +-------------------+-----------------+---------+
    # |               date|             desc|wordCount|
    # +-------------------+-----------------+---------+
    # |2015-05-14 03:53:00|   WARRANT ARREST|        2|
    # |2015-05-14 03:53:00|TRAFFIC VIOLATION|        2|
    # |2015-05-14 03:33:00|TRAFFIC VIOLATION|        2|
    # +-------------------+-----------------+---------+
    df.select(F.sum('wordCount')).show() # 6,count the total number of words in the column across the entire DataFrame
    # squared=F.udf(lambda s:s*s,LongType())
    # df.select(squared('wordCount')).show()
    print(df.columns)        # ['date', 'desc', 'wordCount']
    print(df.dtypes)         # [('date', 'string'), ('desc', 'string'), ('wordCount', 'int')]
    df=df.drop('wordCount')  # drop some column
    
    # data = [
    #     ("2015-05-14 03:10:00", "Sunshine"),
    #     ("2015-05-14 03:00:00", "TRAFFIC VIOLATION"),
    # ]
    # new_df = spark.createDataFrame(data, ["date", "desc"])
    # new_df.join(df,new_df['desc']==df['desc'],'left').show()
    
    df = spark.read.json("resources/people.json")  # DataFrame,每行数据类型是Row,spark.read.text读txt文件也返回DataFrame对象
    df.show()  # Displays the content of the DataFrame to stdout
    # +----+--------+-----+
    # | age|    name|score|
    # +----+--------+-----+
    # |null|Akatsuki|  1.0|
    # |  30|    Andy|  1.5|
    # |  19|  Justin|  2.0|
    # |  19|  Avatar|  2.5|
    # |  19|  Avatar|  4.0|
    # +----+--------+-----+
    print(df.count())  # Number of rows in this DataFrame
    print(df.first())  # First row in this DataFrame
    print(df.collect()) 
    # df[df['name'].contains("t") & df['name'].like('%i%') & (df['age'] > 10)].show()
    # df.select("name").show()  # Select only the "name" column
    # df.select(df['name'], df['age'] + 1).show()      # Select everybody, but increment the age by 1
    # df.select(F.when(df['score']<2,11).when(df['score'] < 3, 22).otherwise(33).alias('new_score')).show()

    # df.printSchema()  # Print the schema in a tree format
    # root
    # |-- age: long (nullable = true)
    # |-- name: string (nullable = true)
    # |-- score: double (nullable = true)

    # df.groupBy(["age"]).count().show()       # Count people by age
    # df.groupBy(['name','age']).avg().show()  # Computes average values for each numeric columns for each group
    df.groupBy(['name','age']).agg(F.count('age'),F.countDistinct('age'),F.mean('score').alias('mean_score')).show() 
    # +--------+----+----------+-------------------+----------+
    # |    name| age|count(age)|count(DISTINCT age)|mean_score|
    # +--------+----+----------+-------------------+----------+
    # |  Justin|  19|         1|                  1|       2.0|
    # |    Andy|  30|         1|                  1|       1.5|
    # |Akatsuki|null|         0|                  0|       1.0|
    # |  Avatar|  19|         2|                  1|      3.25|
    # +--------+----+----------+-------------------+----------+
    
    df.createOrReplaceTempView("people")      # Register the DataFrame as a SQL temporary view
    sqlDF = spark.sql("SELECT * FROM people where age is not null")  # 结尾不要有分号
    # sqlDF.show()

    df.createGlobalTempView("people")      # Register the DataFrame as a global temporary view
    # spark.sql("SELECT * FROM global_temp.people").show()   # Global temporary view is tied to a system preserved database `global_temp`
    # spark.newSession().sql("SELECT * FROM global_temp.people").show()   # Global temporary view is cross-session

def rdd2df(spark):
    # a DataFrame can be created for a JSON dataset represented by an RDD[String] storing one JSON object per string
    json_strings = ['{"name":"Yin","address":{"city":"Columbus","state":"Ohio"}}']
    rdd = spark.sparkContext.parallelize(json_strings)
    df = spark.read.json(rdd)
    df.show()
    # +---------------+----+
    # |        address|name|
    # +---------------+----+
    # |[Columbus,Ohio]| Yin|
    # +---------------+----+

def rdd2df2rdd(spark):
    sc = spark.sparkContext
    lines = sc.textFile("resources/people.txt")     # rdd类型
    parts = lines.map(lambda l: l.split(","))
    people = parts.map(lambda p: Row(name=p[0], age=int(p[1])))
    schemaPeople = spark.createDataFrame(people)      # Infer the schema, and register the DataFrame as a table.
    schemaPeople.createOrReplaceTempView("people")
    df_teenagers = spark.sql("SELECT name FROM people WHERE age >= 13 AND age <= 19")    # The results of SQL queries are Dataframe objects.
    rdd = df_teenagers.rdd
    teenNames = rdd.map(lambda p: "Name: " + p.name)
    print(teenNames.collect())  # List类型 
    # ['Name: Justin'] 

def parquet_schema_merging(spark):
    sc = spark.sparkContext
    squaresDF = spark.createDataFrame(sc.parallelize(range(1, 6)).map(lambda i: Row(single=i, double=i ** 2)))
    squaresDF.write.parquet("data/test_table/key=1")
    cubesDF = spark.createDataFrame(sc.parallelize(range(6, 11)).map(lambda i: Row(single=i, triple=i ** 3))) # adding a new column and dropping an existing column
    cubesDF.write.parquet("data/test_table/key=2")
    mergedDF = spark.read.option("mergeSchema", "true").parquet("data/test_table")     # Read the partitioned table
    mergedDF.printSchema()
    # The final schema consists of all 3 columns in the Parquet files together
    # with the partitioning column appeared in the partition directory paths.
    # root
    #  |-- double: long (nullable = true)
    #  |-- single: long (nullable = true)
    #  |-- triple: long (nullable = true)
    #  |-- key: integer (nullable = true)
    mergedDF.show()
    # +------+------+------+---+
    # |double|single|triple|key|
    # +------+------+------+---+
    # |  null|     9|   729|  2|
    # |  null|    10|  1000|  2|
    # |    16|     4|  null|  1|
    # |    25|     5|  null|  1|
    # |  null|     7|   343|  2|
    # |  null|     6|   216|  2|
    # |  null|     8|   512|  2|
    # |     9|     3|  null|  1|
    # |     1|     1|  null|  1|
    # |     4|     2|  null|  1|
    # +------+------+------+---+

def programmatic_schema(spark):
    sc = spark.sparkContext
    lines = sc.textFile("resources/people.txt")
    parts = lines.map(lambda l: l.split(","))
    # Each line is converted to a tuple.
    people = parts.map(lambda p: (p[0], p[1].strip()))
    # The schema is encoded in a string.
    schemaString = "name age"

    fields = [StructField(field_name, StringType(), True) for field_name in schemaString.split()]
    schema = StructType(fields)

    # Apply the schema to the RDD.
    schemaPeople = spark.createDataFrame(people, schema)
    # Creates a temporary view using the DataFrame
    schemaPeople.createOrReplaceTempView("people")
    # SQL can be run over DataFrames that have been registered as a table.
    results = spark.sql("SELECT name FROM people")
    results.show()
    # +-------+
    # |   name|
    # +-------+
    # |Michael|
    # |   Andy|
    # | Justin|
    # +-------+

def pivot(spark):
    data = [
        (1,'Chinese',80),
        (1,'Math',90),
        (1,'English',100),
        (2,'Chinese',70),
        (2,'Math',80),
        (2,'Chinese',90),
        (3,'English',60),
        (3,'Math',75),
        (3,'English',80),
        (3,'Chinese',95),
    ]
    df = spark.createDataFrame(data,['class','course','score'])
    '''
    There are two versions of pivot function: 
    one that requires the caller to specify the list of distinct values to pivot on, and one that does not. 
    The latter is more concise but less efficient, because Spark needs to first compute the list of distinct values internally.
    '''
    df.groupBy(["class"]).pivot("course",['Chinese','Math','English','11']).sum("score").show()
    
if __name__ == "__main__":
    spark = SparkSession.builder.appName("SparkSQL basic example").config("spark.some.config.option", "some-value").getOrCreate()
    basic_df(spark)
    # rdd2df(spark)
    # rdd2df2rdd(spark)
    # parquet_schema_merging(spark)
    # programmatic_schema(spark)
    spark.stop()
