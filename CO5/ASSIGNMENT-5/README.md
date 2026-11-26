# CSA15 - Cloud Computing and Big Data Analytics | Assignment 5 (CO5)
## Hadoop and MapReduce Architecture Engineering - Metro Transit Footfall Analysis

Everything needed to reproduce Part B of the assignment: source code, configuration, test inputs,
scripts, experiment results, figures and VS Code output screenshots.

```
CO5_Hadoop_Assignment/
|-- README.md
|-- requirements.txt
|-- src/            Python source (generator, mapper, reducer, MapReduce emulator, experiments)
|-- tests/          test_q1.py  (B2.1 validation: hand sample, malformed, boundary, split integrity)
|-- conf/           core-site / hdfs-site / yarn-site / mapred-site / capacity-scheduler XML
|-- schema/         Avro schemas v1 and v2 (device_firmware added with default null)
|-- scripts/        01_hdfs_operations.sh, 02_run_streaming_job.sh, run_all.sh
|-- data/           small test inputs (sample.csv, malformed.csv, empty.csv, exit_only.csv)
|-- results/        captured outputs (*.txt) and raw numbers (*.json)
|-- figures/        diagrams and graphs used in the report
`-- screenshots/    VS Code style screenshots of every Python run
```

## Scenario assumptions
Gate-log record: `timestamp,station_id,gate_id,card_id,tap_type,fare`
(`2026-03-02 08:15:32,S017,G3,C000123456,ENTRY,0.00`), 120 stations (S001-S120), 2 TB/day.
Q1 = tap-ins (ENTRY) per station per hour.  Q2 = five busiest stations per day.

## Quick start
```bash
python -m pip install -r requirements.txt     # only needed for figures/screenshots
python tests/test_q1.py                       # B2.1  (all tests must print PASS)
python src/run_combiner.py                    # B2.2
python src/run_topn.py                        # B2.3
python src/run_scaling.py                     # B3.1  (edit SIZES for bigger files)
python src/run_skew.py                        # B3.2
python src/failure_injection.py               # B4.1
python src/scheduler_sim.py                   # B4.2
bash scripts/run_all.sh                       # everything + figures
```
Hadoop Streaming (real cluster): `bash scripts/02_run_streaming_job.sh`
(mapper.py / reducer.py read stdin and write stdout, so they run unchanged under Hadoop Streaming;
 locally: `cat data/sample.csv | python src/mapper.py | sort | python src/reducer.py`).

## Honest scope statement
* `src/mr_local.py` is a **local emulator** of the MapReduce data path (splits, map-side sort,
  combiner, hash partitioner, shuffle, reduce, counters). Times are wall-clock seconds of one
  Python process - valid for relative comparison only.
* `scheduler_sim.py` is a **model** of FIFO vs Capacity scheduling, not YARN itself.
* NameNode / ResourceManager web-UI captures, `hdfs fsck` output and real job-history logs must be
  captured on a real Hadoop installation (see `scripts/01_hdfs_operations.sh`).
