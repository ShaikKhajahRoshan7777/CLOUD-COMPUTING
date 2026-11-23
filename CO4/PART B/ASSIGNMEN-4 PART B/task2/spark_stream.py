"""Apache Spark Structured Streaming version of Solution B (event-time window + watermark + de-duplication).

Kafka is not available in this sandbox, so micro-batches are delivered through a *file source*: one JSON file per
event, processed with maxFilesPerTrigger=1 (so every event is its own micro-batch, in arrival order).  The
engine, state store, watermark and append-mode semantics are those of Spark itself.  A far-future 'sentinel'
event is appended to advance the watermark so the last real windows are emitted (append mode only emits
a window once the watermark has passed its end).
"""
import json, os, shutil, tempfile
from pyspark.sql import functions as F, types as T

SCHEMA = T.StructType([T.StructField("id", T.StringType()), T.StructField("segment", T.StringType()),
                       T.StructField("speed", T.DoubleType()), T.StructField("ts", T.DoubleType())])


def run_spark_stream(spark, events, watermark_s, tag):
    base = tempfile.mkdtemp(prefix="co4_stream_")
    indir, ckpt = os.path.join(base, "in"), os.path.join(base, "ckpt"); os.makedirs(indir)
    evs = [{k: e[k] for k in ("id", "segment", "speed", "ts")} for e in events]
    evs.append({"id": "SENTINEL", "segment": "SENTINEL", "speed": 0.0, "ts": 100000.0})
    import time
    t0 = time.time() - 10_000
    for i, e in enumerate(evs):         # Spark's file source orders by modification time -> set it explicitly = arrival order
        fp = os.path.join(indir, "%05d.json" % i)
        with open(fp, "w") as f:
            f.write(json.dumps(e))
        os.utime(fp, (t0 + i * 10, t0 + i * 10))
    df = (spark.readStream.schema(SCHEMA).option("maxFilesPerTrigger", 1).json(indir)
          .withColumn("event_time", F.col("ts").cast("timestamp"))
          .withWatermark("event_time", "%d seconds" % watermark_s)
          .dropDuplicatesWithinWatermark(["id"])
          .groupBy(F.window("event_time", "1 minute"), "segment").agg(F.avg("speed").alias("avg_speed")))
    q = (df.writeStream.outputMode("append").format("memory").queryName("res_" + tag)
         .option("checkpointLocation", ckpt).trigger(availableNow=True).start())
    q.awaitTermination()
    rows = spark.sql("SELECT segment, CAST(unix_timestamp(window.start) AS DOUBLE) AS ws, avg_speed FROM res_" + tag).collect()
    shutil.rmtree(base, ignore_errors=True)
    return {(r["segment"], int(r["ws"])): round(r["avg_speed"], 4) for r in rows if r["segment"] != "SENTINEL"}
