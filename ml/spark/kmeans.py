import numpy as np
import matplotlib.pyplot as plt
from pyspark.sql import SparkSession

def generate_data():
    plt.subplot(1, 2, 1)
    X1 = 2 * np.random.random(40)  # [0,2]
    Y1 = 2 * np.random.random(40)  # [0,2]
    plt.scatter(X1, Y1, s=10, c='green')

    X2 = 2.5 + 1.5 * np.random.random(80)  # [2.5,4]
    Y2 = .5 + 2 * np.random.random(80)     # [.5,2.5]
    plt.scatter(X2, Y2, s=10, c='green')

    X3 = np.random.random(40)        # [0,1]
    Y3 = 2.5 + np.random.random(40)  # [2.5,3.5]
    plt.scatter(X3, Y3, s=10, c='green')

    X4 = 3 + np.random.random(60)  # [3,4]
    Y4 = 3 + np.random.random(60)  # [3,4]
    plt.scatter(X4, Y4, s=10, c='green')

    X = np.hstack((X1,X2,X3,X4))
    Y = np.hstack((Y1,Y2,Y3,Y4))
    return 4,np.vstack((X,Y)).T

def closest_point(p, centers):
    bestIndex = 0
    closest = float("+inf")
    for i in range(len(centers)):
        tempDist = np.sum((p - centers[i]) ** 2)
        if tempDist < closest:
            closest = tempDist
            bestIndex = i
    return bestIndex

def kmeans(spark,data,K,converge_dist=.001):
    temp_dist = float('inf')
    rdd_data = spark.sparkContext.parallelize(data).cache() # 每行需要是ndarray类型
    kPoints = rdd_data.takeSample(False, K)    # False代表不放回采样
    while temp_dist > converge_dist:
        closest = rdd_data.map( lambda p: (closest_point(p, kPoints), (p, 1)) )
        stats = closest.reduceByKey(lambda x, y: (x[0] + y[0], x[1] + y[1]))
        newPoints = stats.map(lambda st: (st[0], st[1][0] / st[1][1])).collect()
        temp_dist = sum(np.sum((kPoints[iK] - p) ** 2) for iK, p in newPoints)
        for iK, p in newPoints:
            kPoints[iK] = p
    print(f"Final centers: {kPoints}")

    plt.subplot(1, 2, 2)
    _ = {idx:[] for idx in range(K)}
    for item in closest.collect():
        _[item[0]].append(item[1][0])
    for key in _:
        points=np.array(_[key])
        plt.scatter(points[:,0],points[:,1],s=10)
    plt.show()

if __name__ == "__main__":
    spark = SparkSession.builder.appName("KMeans").getOrCreate()
    K,data = generate_data()
    kmeans(spark,data,K)
    spark.stop()
