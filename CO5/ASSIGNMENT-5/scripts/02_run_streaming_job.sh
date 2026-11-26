#!/usr/bin/env bash
# Q1 on Hadoop Streaming (with and without combiner). Adjust STREAMING_JAR for your install.
STREAMING_JAR=$HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-*.jar
for MODE in with without; do
  hdfs dfs -rm -r -f /transit/out_$MODE
  COMB=""; [ $MODE = with ] && COMB="-combiner reducer.py"
  hadoop jar $STREAMING_JAR \
    -D mapreduce.job.reduces=2 \
    -files ../src/mapper.py,../src/reducer.py,../src/transit_mr.py \
    -mapper "python3 mapper.py" -reducer "python3 reducer.py" $COMB \
    -input /transit/raw/gate_1gb.csv -output /transit/out_$MODE 2>&1 | tee ../results/streaming_$MODE.log
done
