import numpy as np
import pandas as pd
from pyspark.sql import SparkSession,Window
from pyspark.sql.functions import pandas_udf,PandasUDFType,ceil
from pyspark.sql.types import LongType

def dataframe_with_arrow(spark):
    spark.conf.set("spark.sql.execution.arrow.enabled", "true")  # Enable Arrow-based columnar data transfers
    pdf = pd.DataFrame(np.random.rand(100, 3))                   # Generate a Pandas DataFrame
    df = spark.createDataFrame(pdf)                              # Create a Spark DataFrame from a Pandas DataFrame using Arrow
    result_pdf = df.select("*").toPandas()                       # Convert the Spark DataFrame back to a Pandas DataFrame using Arrow
    print(f"Pandas DataFrame result statistics:\n{result_pdf.describe()}\n")

def scalar_pandas_udf(spark):
    multiply = pandas_udf(lambda a,b: a * b, returnType=LongType())
    df = spark.createDataFrame(pd.DataFrame(pd.Series([1, 2, 3]), columns=["x"]))
    df.select(multiply("x", "x")).show()  # Execute function as a Spark vectorized UDF
    # +--------------+
    # |<lambda>(x, x)|
    # +--------------+
    # |             1|
    # |             4|
    # |             9|
    # +--------------+

def grouped_map_pandas_udf(spark):
    @pandas_udf("id long, v double", functionType=PandasUDFType.GROUPED_MAP)  # functionType: an enum value in pyspark.sql.functions.PandasUDFType, Default SCALAR
    def subtract_mean(pdf):
        v = pdf.v          # pdf is a pandas.DataFrame
        return pdf.assign(v=v - v.mean())  # 添加新的列或者覆盖原有的列

    @pandas_udf("id long, v double", PandasUDFType.GROUPED_MAP)
    def mean_udf(key, pdf):
        # key is a tuple of one numpy.int64, which is the value of 'id' for the current group
        return pd.DataFrame([key + (pdf['v'].mean(),)])

    @pandas_udf("id long, `ceil(v / 2)` long, v double",PandasUDFType.GROUPED_MAP)
    def sum_udf(key, pdf):
        # key is a tuple of two numpy.int64s, which is the values of 'id' and 'ceil(df.v / 2)' for the current group
        return pd.DataFrame([key + (pdf['v'].sum(),)])

    df = spark.createDataFrame([(1, 1.0), (1, 2.0), (2, 3.0), (2, 5.0), (2, 10.0)],("id", "v"))
    df.groupBy("id").apply(subtract_mean).show()
    # +---+----+
    # | id|   v|
    # +---+----+
    # |  1|-0.5|
    # |  1| 0.5|
    # |  2|-3.0|
    # |  2|-1.0|
    # |  2| 4.0|
    # +---+----+

    df.groupBy('id').apply(mean_udf).show()
    # +---+---+
    # | id|  v|
    # +---+---+
    # |  1|1.5|
    # |  2|6.0|
    # +---+---+

    df.groupBy('id', ceil(df['v'] / 2)).apply(sum_udf).show()
    # +---+-----------+----+
    # | id|ceil(v / 2)|   v|
    # +---+-----------+----+
    # |  2|          5|10.0|
    # |  1|          1| 3.0|
    # |  2|          3| 5.0|
    # |  2|          2| 3.0|
    # +---+-----------+----+

def grouped_agg_pandas_udf(spark):
    df = spark.createDataFrame([(1, 1.0), (1, 2.0), (2, 3.0), (2, 5.0), (2, 10.0)],("id", "v"))

    @pandas_udf("double", PandasUDFType.GROUPED_AGG)
    def mean_udf(v):
        return v.mean()
    df.groupBy("id").agg(mean_udf(df['v'])).show()
    # +---+-----------+
    # | id|mean_udf(v)|
    # +---+-----------+
    # |  1|        1.5|
    # |  2|        6.0|
    # +---+-----------+

    w = Window.partitionBy('id').rowsBetween(Window.unboundedPreceding, Window.unboundedFollowing)
    df.withColumn('mean_v', mean_udf(df['v']).over(w)).show()
    # +---+----+------+
    # | id|   v|mean_v|
    # +---+----+------+
    # |  1| 1.0|   1.5|
    # |  1| 2.0|   1.5|
    # |  2| 3.0|   6.0|
    # |  2| 5.0|   6.0|
    # |  2|10.0|   6.0|
    # +---+----+------+

if __name__ == "__main__":
    spark = SparkSession.builder.appName("Python Arrow-in-Spark example").getOrCreate()
    # dataframe_with_arrow(spark)
    # scalar_pandas_udf(spark)
    grouped_map_pandas_udf(spark)
    # grouped_agg_pandas_udf(spark)
    spark.stop()