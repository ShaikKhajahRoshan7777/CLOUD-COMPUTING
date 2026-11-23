"""Same job on real Apache Spark (local mode) with stage / shuffle evidence from the Spark REST API."""
import json, os, time, urllib.request
from pyspark.sql import SparkSession, functions as F


def spark_session(shuffle_partitions=4):
    return (SparkSession.builder.master("local[2]").appName("co4-task1")
            .config("spark.sql.shuffle.partitions", str(shuffle_partitions))
            .config("spark.sql.adaptive.enabled", "false")
            .config("spark.driver.memory", "1500m")
            .config("spark.ui.showConsoleProgress", "false").getOrCreate())


def quiet(spark):
    spark.sparkContext.setLogLevel("ERROR")
    return spark


def run_spark(spark, path, n_input_parts=8):
    size = os.path.getsize(path)
    spark.conf.set("spark.sql.files.maxPartitionBytes", str(max(size // n_input_parts, 1 << 20)))
    t0 = time.perf_counter()
    raw = spark.read.csv(path, header=True, inferSchema=False)
    sp = F.expr("try_cast(speed AS DOUBLE)")      # ANSI mode: invalid text -> NULL instead of an error
    ts = F.try_to_timestamp(F.col("event_time"), F.lit("yyyy-MM-dd HH:mm:ss"))
    valid = sp.isNotNull() & ts.isNotNull() & (sp >= 0) & (sp <= 200)
    df = raw.select(F.when(valid, F.col("segment")).alias("segment"),
                    F.when(valid, F.date_format(ts, "yyyy-MM-dd HH")).alias("hour"), sp.alias("speed"))
    # rejected rows collapse into the (null, null) group -> one job gives avg AND counts
    out = (df.groupBy("segment", "hour").agg(F.avg("speed").alias("avg_speed"), F.count(F.lit(1)).alias("n"))
             .collect())
    elapsed = time.perf_counter() - t0
    rejected = sum(r["n"] for r in out if r["segment"] is None)
    accepted = sum(r["n"] for r in out if r["segment"] is not None)
    avg = {(r["segment"], r["hour"]): r["avg_speed"] for r in out if r["segment"] is not None}
    return avg, {"read": accepted + rejected, "accepted": accepted, "rejected": rejected,
                 "seconds": elapsed, "stages": stage_metrics(spark)}


def stage_metrics(spark):
    sc = spark.sparkContext
    url = "%s/api/v1/applications/%s/stages?status=complete" % (sc.uiWebUrl, sc.applicationId)
    try:
        stages = json.load(urllib.request.urlopen(url, timeout=10))
    except Exception as e:                       # UI disabled / unreachable
        return [{"error": str(e)}]
    return [{"stage_id": s["stageId"], "name": s["name"].split(" at ")[0][:28], "tasks": s["numTasks"],
             "run_time_s": round(s["executorRunTime"] / 1000, 2), "input_mb": round(s["inputBytes"] / 1e6, 2),
             "shuffle_write_kb": round(s["shuffleWriteBytes"] / 1e3, 1),
             "shuffle_read_kb": round(s["shuffleReadBytes"] / 1e3, 1)} for s in sorted(stages, key=lambda x: x["stageId"])]
