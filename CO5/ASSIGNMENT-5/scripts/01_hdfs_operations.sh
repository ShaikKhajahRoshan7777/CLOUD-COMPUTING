#!/usr/bin/env bash
# B1 - deploy check + HDFS operations (run on the Hadoop node). Save output with:  bash 01_hdfs_operations.sh | tee ../results/hdfs_session.txt
set -x
hdfs namenode -format -force
start-dfs.sh && start-yarn.sh
jps                                              # expect NameNode, DataNode, SecondaryNameNode, ResourceManager, NodeManager
hdfs dfsadmin -report | head -20
# NameNode UI: http://localhost:9870    ResourceManager UI: http://localhost:8088
hdfs dfs -mkdir -p /transit/raw /transit/out
python3 ../src/generate_logs.py /tmp/gate_1gb.csv --size-mb 1024
hdfs dfs -put /tmp/gate_1gb.csv /transit/raw/
hdfs dfs -ls -h /transit/raw
hdfs dfs -du -h /transit
hdfs dfs -df -h /
hdfs dfs -setrep -w 2 /transit/raw/gate_1gb.csv
hdfs fsck /transit/raw/gate_1gb.csv -files -blocks -locations
# B1.3 data in / out
hdfs dfs -put ../data/sample.csv /transit/raw/
sqoop import --connect jdbc:mysql://localhost/transit --table fare_table --target-dir /transit/fare -m 1   # needs Sqoop + MySQL
hdfs dfs -get /transit/out/part-00000 ./q1_result.txt
