import numpy as np
from pyspark.sql import SparkSession

def closest_point(p, centers):
    bestIndex = 0
    closest = float("+inf")
    for i in range(len(centers)):
        tempDist = np.sum((p - centers[i]) ** 2)
        if tempDist < closest:
            closest = tempDist
            bestIndex = i
    return bestIndex

def kmeans(spark,K,converge_dist=.01):
    temp_dist = 1
    lines = spark.sparkContext.parallelize([
        '2 1 4',
        '-1 -5 5',
        '6 8 23',
        '0 9 3',
        '2 52 2',
        '1 4 2',
        '4 5 1',
        '4 4 4',
        '3 6 7',
        '4 7 6',
        '6 8 89',
        '8 8 9',
        '3 82 3',
        '2 90 2',
    ])  
    data = lines.map(lambda line: np.array([float(x) for x in line.split(' ')])).cache()  # rdd,注意要转换成ndarray类型
    kPoints = data.takeSample(False, K)    # False代表不放回采样
    while temp_dist > converge_dist:
        closest = data.map( lambda p: (closest_point(p, kPoints), (p, 1)) )
        stats = closest.reduceByKey(lambda x, y: (x[0] + y[0], x[1] + y[1]))
        print(stats.collect())
        newPoints = stats.map(lambda st: (st[0], st[1][0] / st[1][1])).collect()
        print(newPoints)
        temp_dist = sum(np.sum((kPoints[iK] - p) ** 2) for iK, p in newPoints)
        for iK, p in newPoints:
            kPoints[iK] = p
    print(f"Final centers: {kPoints}")
    
if __name__ == "__main__":
    spark = SparkSession.builder.appName("KMeans").getOrCreate()
    kmeans(spark,3)
    spark.stop()
