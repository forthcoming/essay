from pyspark.sql import SparkSession
from pyspark.sql import Row
from pyspark.sql.types import *

# DataFrame的每一行类型是Row

def json_string(spark):
    # a DataFrame can be created for a JSON dataset represented by an RDD[String] storing one JSON object per string
    jsonStrings = ['{"name":"Yin","address":{"city":"Columbus","state":"Ohio"}}']
    otherPeopleRDD = spark.sparkContext.parallelize(jsonStrings)
    otherPeople = spark.read.json(otherPeopleRDD)
    otherPeople.show()
    # +---------------+----+
    # |        address|name|
    # +---------------+----+
    # |[Columbus,Ohio]| Yin|
    # +---------------+----+

def basic_df_example(spark):
    df = spark.read.json("resources/people.json")
    # df.show()  # Displays the content of the DataFrame to stdout
    # +----+-------+
    # | age|   name|
    # +----+-------+
    # |null|Michael|
    # |  30|   Andy|
    # |  19| Justin|
    # +----+-------+

    # df.printSchema()  # Print the schema in a tree format
    # root
    # |-- age: long (nullable = true)
    # |-- name: string (nullable = true)

    # df.select("name").show()  # Select only the "name" column
    # +-------+
    # |   name|
    # +-------+
    # |Michael|
    # |   Andy|
    # | Justin|
    # +-------+

    # df.select(df['name'], df['age'] + 1).show()      # Select everybody, but increment the age by 1
    # +-------+---------+
    # |   name|(age + 1)|
    # +-------+---------+
    # |Michael|     null|
    # |   Andy|       31|
    # | Justin|       20|
    # +-------+---------+

    # df.filter(df['age'] > 21).show()      # Select people older than 21
    # +---+----+
    # |age|name|
    # +---+----+
    # | 30|Andy|
    # +---+----+

    df.groupBy(df["age"]).count().show()      # Count people by age
    # +----+-----+
    # | age|count|
    # +----+-----+
    # |  19|    1|
    # |null|    1|
    # |  30|    1|
    # +----+-----+

    df.createOrReplaceTempView("people")      # Register the DataFrame as a SQL temporary view
    sqlDF = spark.sql("SELECT * FROM people where age is not null")  # 结尾不要有分号
    # sqlDF.show()
    # +----+-------+
    # | age|   name|
    # +----+-------+
    # |  30|   Andy|
    # |  19| Justin|
    # +----+-------+

    df.createGlobalTempView("people")      # Register the DataFrame as a global temporary view
    # spark.sql("SELECT * FROM global_temp.people").show()   # Global temporary view is tied to a system preserved database `global_temp`
    # +----+-------+
    # | age|   name|
    # +----+-------+
    # |null|Michael|
    # |  30|   Andy|
    # |  19| Justin|
    # +----+-------+

    # spark.newSession().sql("SELECT * FROM global_temp.people").show()   # Global temporary view is cross-session
    # +----+-------+
    # | age|   name|
    # +----+-------+
    # |null|Michael|
    # |  30|   Andy|
    # |  19| Justin|
    # +----+-------+

def schema_inference_example(spark):
    sc = spark.sparkContext
    lines = sc.textFile("resources/people.txt")     # Load a text file and convert each line to a Row.
    parts = lines.map(lambda l: l.split(","))
    people = parts.map(lambda p: Row(name=p[0], age=int(p[1])))
    schemaPeople = spark.createDataFrame(people)      # Infer the schema, and register the DataFrame as a table.
    schemaPeople.createOrReplaceTempView("people")
    teenagers = spark.sql("SELECT name FROM people WHERE age >= 13 AND age <= 19")    # The results of SQL queries are Dataframe objects.
    teenNames = teenagers.rdd.map(lambda p: "Name: " + p.name).collect()     # rdd returns the content as an :class:`pyspark.RDD` of :class:`Row`.
    for name in teenNames:
        print(name)
    # Name: Justin


def programmatic_schema_example(spark):
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

if __name__ == "__main__":
    spark = SparkSession.builder.appName("Python Spark SQL basic example").config("spark.some.config.option", "some-value").getOrCreate()
    basic_df_example(spark)
    # schema_inference_example(spark)
    # programmatic_schema_example(spark)
    spark.stop()