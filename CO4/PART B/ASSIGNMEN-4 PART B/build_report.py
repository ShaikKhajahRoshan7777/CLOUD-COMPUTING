"""Builds the final Word report: ORIGINAL pages kept byte-for-byte in the document body, new report appended after them."""
import json, os, sys, glob, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from docx import Document
from report_helpers import *

ROOT = os.path.dirname(os.path.abspath(__file__)); R = lambda n: json.load(open(os.path.join(ROOT, "results", n)))
SS = lambda n: os.path.join(ROOT, "screenshots", n); FG = lambda n: os.path.join(ROOT, "figures", n)
SRC = sys.argv[1]; OUT = sys.argv[2]
doc = Document(SRC); rp = Report(doc)
t1, t2, t3, t4, t5, t6 = (R("task%d_results.json" % i) for i in range(1, 7))
env = t1["env"]
f2 = lambda x: "%.2f" % x; f3 = lambda x: "%.3f" % x

def consoles(task, label):
    for i, pth in enumerate(sorted(glob.glob(SS("task%d_console_*.png" % task))), 1):
        rp.image(pth, "%s - console output (VS Code terminal view), part %d" % (label, i), 6.2)

# ============================================================ cover banner + overview
rp.page_break()
rp.banner([("CSA15 \u2013 CLOUD COMPUTING AND BIG DATA ANALYTICS", 14, "FFFFFF"), ("ASSIGNMENT 4 \u2013 PART II  |  CO4 IMPLEMENTATION REPORT", 12, "DCE6F2"),
           ("Big Data Engineering: Implement, Test, Secure & Scale", 12, "FFFFFF"), ("Six tasks \u2022 every number in this report comes from a program run whose console log is included", 10, "DCE6F2")])
rp.h1("1. Executive Summary")
rp.p("This report answers all six tasks of Assignment 4 \u2013 Part II (50 marks). Every task follows the mandatory evidence chain: **Configuration / Source Code \u2192 Test Data \u2192 Expected Behaviour \u2192 Actual Output \u2192 Intermediate Evidence \u2192 Boundary / Failure Test \u2192 Interpretation**. Predictions were written to a file **before** the run that tested them, and where a prediction was wrong this report says so and explains why.")
rp.table([["Task", "Marks", "What was built", "Headline measured result"],
          ["1  Batch pipeline", "8", "Map / shuffle / reduce with combiner + the same job on Apache Spark %s" % env.get("pyspark", ""), "Map stage = 99% of time at 4M rows; combiner cut shuffle from 3,840,098 to 38,400 records; results match an independent pandas check (max error 2.8e-14)"],
          ["2  Batch vs stream", "9", "Batch engine, event-time streaming engine (watermark, de-dup, checkpoint) + Spark Structured Streaming", "Counterexample: window [0,60) = 48.0 (batch) vs 56.0 (stream); caused first by a duplicate whose ID was already evicted, then by a late event"],
          ["3  Security & privacy", "10", "Role views + hash-chained audit, linkage attack, k-anonymity lattice, AES-256-GCM + HMAC + SHA-256", "Attack re-identified 2,983 of 5,000 people (predicted 2,980); after generalisation k = 5 and 0 re-identifiable; encryption cost +295% time"],
          ["4  Data quality", "7", "5-rule cleaning stage with quarantine, decision trace, drift monitor", "40% duplicates: kept rows unchanged, shuffle \u00d71.58 (as predicted), run time \u00d71.99 (predicted \u00d71.58); m/s drift detected by median ratio 0.278"],
          ["5  Storage models", "7", "5,000,010 events in CSV, Parquet, SQLite", "Q1 reads 100% / 2.2% / 0.3% of the store; Parquet is 8.8\u00d7 smaller than CSV; SQLite ingest 31k events/s vs ~840k for append-only"],
          ["6  Fraud-link detector", "9", "Naive O(n\u00b2) vs keyed sliding window, hand-checked 20-event test", "10M events in 11.0 s (keyed) vs 1,630 h projected (naive); one hot account puts 56% of events in one partition"]],
         [1.15, 0.6, 2.1, 2.42], "Summary of the six tasks")
rp.callout("Honest scope note.", "All programs were executed on one machine (%s, %d core, %.1f GB RAM, Python %s, Spark in local mode). They were **not** run on Zoho, Azure or GCP, and Kafka was not available, so Spark Structured Streaming was fed through its file source. The eight events of Part I Task 6 were not available to the author, so a documented placeholder set is used (replaceable in tests/part1_events.json). Screenshots are renders of the real console logs in a VS Code layout; the same commands can be re-run in VS Code to capture native screenshots." % (env.get("cpu", "x86-64 CPU"), env.get("cpu_cores", 1), env.get("ram_gb", 4), env.get("python", "3")), "FFF4E5", ORANGE)

rp.h1("2. Environment and Repository Layout")
rp.table([["Item", "Value"], ["Hardware", "%s, %d core, %.1f GB RAM" % (env.get("cpu", ""), env.get("cpu_cores", 1), env.get("ram_gb", 4))], ["Operating system", env.get("os", "")],
          ["Python / libraries", "Python %s, pandas %s, NumPy %s, PyArrow %s, PySpark %s, cryptography %s, SQLite 3.45.1" % (env.get("python"), env.get("pandas"), env.get("numpy"), env.get("pyarrow"), env.get("pyspark"), env.get("cryptography"))],
          ["Java (for Spark)", "OpenJDK 21"], ["Timing method", "time.perf_counter(); each measurement repeated at least 3 times and reported as mean \u00b1 standard deviation unless stated"], ["Random seeds", "Fixed in every generator (42, 7, 2026, 17, 3, 8 ...) so every run is reproducible"]],
         [1.6, 4.67], "Experimental environment")
rp.table([["Folder / file", "Purpose"], ["run_task1.py \u2026 run_task6.py", "One entry point per task; prints the evidence shown in this report"], ["task1/ \u2026 task6/", "Task-specific modules (generators, engines, algorithms)"],
          ["common/utils.py", "Environment report, repeated timing, JSON results"], ["results/", "Console logs, JSON results and the saved predictions (task*_prediction*.json)"],
          ["figures/  screenshots/", "Charts and VS Code-style output images used in this report"], ["tests/part1_events.json", "Replaceable eight-event test for Task 6.3"], ["README.md, requirements.txt, run_all.sh", "How to reproduce everything"]],
         [2.2, 4.07], "Repository layout (the folder to upload to GitHub)")

# ============================================================ TASK 1
rp.page_break(); rp.h1("TASK 1 \u2013 Build and Validate a Batch Processing Pipeline (8 Marks)")
rp.h2("Configuration and source code")
rp.p("Problem: average speed per road segment per hour from a large file of events (Sensor ID, Segment, Speed, Event Time). The implementation in task1/mapreduce.py is a faithful map / shuffle / reduce: the file is cut into **8 byte-range input splits** (Hadoop rule: a split owns the lines that start inside it); each **map** task parses and validates lines and emits ((segment, hour), (sum, count)) with a **combiner**; the **shuffle** hash-partitions (CRC32) the partial results to **4 reducers** and serialises them; each **reduce** merges partial sums and emits the average. The same job was also run on real **Apache Spark %s** (local[2], 4 shuffle partitions) and its stages were read from the Spark REST API." % env.get("pyspark", ""))
rp.image(SS("task1_code.png"), "Core of task1/mapreduce.py (parse_line, map_stage, shuffle_stage, reduce_stage)", 5.2)
rp.h2("Test data and generator")
rp.p("task1/gen_traffic.py (seed 42) creates 200 segments \u00d7 5 sensors over 24 hours with speeds ~ Normal(45 + 4\u00b7(segment mod 7), 12). About **2% null speeds, 1% out-of-range speeds (\u22125, 250, 999) and 1% malformed timestamps** are injected, so rejection paths are exercised. An optional hot_share parameter sends a fraction of events to one segment (used for the skew test). Three sizes in the ratio 1 : 5 : 20 were generated: 200,000 rows (7.6 MB), 1,000,000 rows (37.8 MB) and 4,000,000 rows (151.3 MB). The reference answer is computed by an independent chunked pandas program that shares no code with the pipeline.")
rp.h2("Expected behaviour (predictions recorded before the runs)")
cmp_ = t1["compare"]
rp.table([["Size", "Dominant stage (pred / obs)", "Shuffle records with combiner (pred / obs)", "Shuffle records without combiner (pred / obs)", "Run-time ratio vs 200k (pred / obs)"]] +
         [[c["size"], "%s / %s" % (c["dominant_pred"], c["dominant_obs"]), "%d / %d" % (c["shuffle_pred"], c["shuffle_obs"]), "%d / %d" % (c["nocomb_pred"], c["nocomb_obs"]), "%.0f / %.1f" % (c["ratio_pred"], c["ratio_obs"])] for c in cmp_],
         [1.0, 1.15, 1.45, 1.45, 1.22], "Task 1.3 \u2013 predictions compared with observations")
rp.p("Reasoning behind the predictions: parsing every line dominates, so the map stage should stay dominant; with a combiner each split sends at most one record per (segment, hour) key, so shuffle records are bounded by 8 \u00d7 4,800 keys (balls-in-bins estimate 38,141 at 200k rows) and stop growing; without it shuffle equals accepted records (linear); time should scale about linearly with rows.")
rp.h2("Actual output")
o = t1["observed"]
rp.table([["Size", "Read", "Accepted", "Rejected", "Map s", "Shuffle s", "Reduce s", "Total s (mean \u00b1 SD, n=3)"]] +
         [[k.split(" (")[0], "{:,}".format(v["read"]), "{:,}".format(v["accepted"]), "{:,}".format(v["rejected"]), f3(v["stage_mean"]["map"]), f3(v["stage_mean"]["shuffle"]), f3(v["stage_mean"]["reduce"]), "%.2f \u00b1 %.2f" % (v["total_mean"], v["total_sd"])] for k, v in o.items()],
         [0.55, 0.85, 0.85, 0.75, 0.6, 0.7, 0.7, 1.27], "Records read / accepted / rejected and time per stage (8 splits, 4 reducers)", align_right_from=1)
L = o["L (4M rows)"]
rp.table([["Reducer", "Raw records", "Partial records (after combiner)", "Distinct keys"]] + [["reducer %d" % i, "{:,}".format(l["raw_records"]), "{:,}".format(l["partial_records"]), "{:,}".format(l["keys"])] for i, l in enumerate(L["reducer_load"])],
         [1.2, 1.5, 2.2, 1.37], "Records per reducer at 4,000,000 rows", align_right_from=1)
rp.p("Correctness: all 4,800 (segment, hour) averages agree with the pandas reference (maximum absolute error 2.84e-14) at all three sizes, and read = accepted + rejected in every run. **Single-process comparison:** on a separate 10,000-row sample a plain dictionary loop and the map/shuffle/reduce job returned identical results (same keys, difference below 1e-9).")
rp.h2("Intermediate evidence: stages, partitions, shuffle and where the cost lies")
sp = t1["spark"]
rows = [["Size / run", "Stage", "Tasks (partitions)", "Run time s", "Input MB", "Shuffle write KB", "Shuffle read KB"]]
for k, v in sp.items():
    for s in v["stages"]: rows.append([k.split(" (")[0], "%d %s" % (s["stage_id"], s["name"]), s["tasks"], s["run_time_s"], s["input_mb"], s["shuffle_write_kb"], s["shuffle_read_kb"]])
rp.table(rows, [0.75, 1.05, 0.95, 0.8, 0.7, 1.0, 1.02], "Apache Spark stage evidence from the REST API (same job, same files)", align_right_from=2)
rp.p("**Meaning of each observation.** (1) The Spark job has three stages: a tiny CSV-header stage, then a **map stage with 8\u20139 tasks** (one per input split; it scans, parses and pre-aggregates; this is where all the input bytes are read) and a **reduce stage with 4 tasks** (equal to spark.sql.shuffle.partitions). (2) The data crossing the stage boundary is only 632 KB, 690 KB and 745 KB for inputs of 8, 38 and 152 MB: the partial aggregation makes the shuffle almost independent of the input size, exactly as the prediction expected. (3) In the hand-written job, map = 90%, 98% and 99% of total time for the three sizes, shuffle \u2248 0.05 s and reduce \u2248 0.02 s, so **the dominant cost is reading and parsing in the map stage, not the shuffle**. (4) Without the combiner the shuffle would move 192,078 / 959,749 / 3,840,098 records (8.1 / 40.3 / 161.3 MB serialised) instead of 38,135 / 38,400 / 38,400 records (about 1.6 MB), i.e. a 100\u00d7 reduction at 4M rows. Spark times: 4.2 \u00b1 4.2 s (200k, includes JVM warm-up in the first run), 3.3 \u00b1 0.3 s (1M, n=3) and 9.3 s (4M, one run).")
rp.image(FG("fig_task1.png"), "Task 1: (a) time per stage, (b) shuffle volume with and without combiner, (c) skew test", 6.27)
rp.h2("Requirement change \u2013 interpretation of the scaling runs")
rp.p("The dominant stage did **not** change (map at every size), and the shuffle volume with the combiner plateaued at 38,400 records, both as predicted. Run time grew \u00d71 : \u00d74.6 : \u00d717.0 for data growing \u00d71 : \u00d75 : \u00d720, slightly **better than linear** (prediction \u00d75 and \u00d720): a fixed start-up cost of roughly 0.1 s per job is amortised over more rows. A prediction that would have failed is the shuffle volume **without** a combiner, which scales linearly (\u00d75, \u00d720) \u2013 the combiner is what makes the design scale.")
rp.h2("Boundary / failure tests")
rows = [["Case", "Result", "Observation"]] + [[b["case"], "PASS" if b["pass"] else "FAIL", b["detail"]] for b in t1["boundary"]]
rp.table(rows, [2.5, 0.6, 3.17], "Boundary tests B1\u2013B7, each checked against a value computed by hand")
sk = t1["skew"]
rp.p("**Chosen boundary case B8 \u2013 data skew.** A single segment holding most of the data is the classic way a MapReduce job silently becomes a one-machine job, so 90%% of 1,000,000 events were placed on segment SEG000. Observation: without a combiner the reducer loads were %s records (max/mean = %.2f); with the combiner the loads were %s. The reduce stage took %.3f s without and %.3f s with the combiner, and the shuffle carried %s vs %s records. The imbalance is mild (1.15) only because the key is **(segment, hour)** \u2013 the hot segment is spread over 24 keys; had the key been the segment alone, one reducer would have received about 90%% of the records. The combiner removes the imbalance entirely by shrinking each hot key to one partial record per split. **No defect was exposed in correctness (all 8 cases pass); the skew test exposed a scaling risk that the combiner and a composite key mitigate.**" % (sk["loads_nocomb"], sk["imbalance_nocomb"], sk["loads_comb"], sk["reduce_s_nocomb"], sk["reduce_s_comb"], "{:,}".format(sk["shuffle_nocomb"]), "{:,}".format(sk["shuffle_comb"])))
consoles(1, "Task 1")

# ============================================================ TASK 2
rp.page_break(); rp.h1("TASK 2 \u2013 Batch vs Stream: Build It, Break It, Explain It (9 Marks)")
rp.h2("Configuration and source code")
rp.p("**Solution A (batch)** reads all stored events, drops duplicate event IDs and averages speed per (segment, one-minute event-time window). **Solution B (stream)** is an event-time engine (task2/engines.py) with three settings under study: the **window** (60 s tumbling), the **watermark** (allowed lateness; watermark = maximum event time seen \u2212 lateness) and the **de-duplication retention** (how long an event ID is remembered). An event is dropped as late when its window end is at or below the watermark; a window is emitted when the watermark passes its end (append mode); state can be checkpointed and restored. The same logic was also executed in **Spark Structured Streaming** (withWatermark + dropDuplicatesWithinWatermark + window aggregation, append mode, one micro-batch per event through the file source).")
rp.image(SS("task2_code.png"), "Core of task2/engines.py \u2013 the streaming engine", 5.4)
rp.h2("2.1 Normal case \u2013 results side by side")
rp.p("Test data: 90 ordered, clean events (5 minutes \u00d7 3 segments \u00d7 6 events), each arriving 1 s after it happened, no duplicates. Both solutions produced **identical values for all 15 windows** (full side-by-side listing in the console screenshot below), so the two implementations agree when their assumptions hold.")
rp.h2("2.2 Break the stream \u2013 student-designed counterexample")
ce_b, ce_s = t2["break"]["batch"], t2["break"]["stream"]
rp.table([["Event", "Event time (s)", "Arrival (s)", "Speed", "Property"],
          ["e1, e2, e3", "5, 20, 35", "6, 21, 36", "40, 50, 60", "normal"], ["e4", "65", "66", "70", "advances the watermark to 55 s"],
          ["e2 (2nd copy)", "20", "67", "50", "**duplicate** re-delivered while window [0,60) is still open"], ["e5", "58", "68", "80", "out of order by 7 s but inside the 10 s watermark (must be kept)"],
          ["e8, e6", "100, 50", "101, 102", "20, 10", "**e6 is late**: window [0,60) was closed when e8 raised the watermark to 90 s"], ["e9, e10, e11", "130, 190, 200", "131, 191, 201", "30, 90, 55", "normal"]],
         [1.0, 1.0, 1.0, 0.8, 2.47], "Hand-designed events (one segment A; window 60 s, watermark 10 s, de-dup retention 30 s)")
rp.table([["Window", "BatchResult", "StreamResult", "Equal?"]] + [[k.replace("('A', ", "A [").replace(")", ", +60)"), ce_b[k], ce_s[k], "yes" if ce_b[k] == ce_s[k] else "**NO**"] for k in ce_b], [1.8, 1.5, 1.5, 1.47], "StreamResult \u2260 BatchResult", align_right_from=1)
rp.callout("Finding.", "The window [0,60) differs: batch = 48.0 = (40+50+60+80+10)/5 but stream = 56.0 = (40+50+60+50+80)/5. **First responsible event: the duplicate copy of e2 (arrival t = 67 s).** Because the de-duplication retention was only 30 s of event time, the ID of e2 (event time 20 s) had already been forgotten when the copy arrived, although the window was still open, so it was counted twice. **The setting responsible: de-duplication retention shorter than the window lifetime.** The second error is e6, dropped because the 10 s watermark had already closed its window.")
fx = t2["break"]["fixes"]
rp.table([["Change tried (one at a time)", "StreamResult vs BatchResult"]] + [[f["label"], "equal" if f["equal"] else "**still different**"] for f in fx], [4.6, 1.67], "Fix attempts")
rp.p("**Fix and its cost.** Neither setting alone is enough: raising the watermark to 60 s fixes the late event but not the duplicate (retention still 30 s), and keeping IDs until the window closes fixes the duplicate but not the late event. Both together give StreamResult = BatchResult. The smallest working watermark is **41 s** (40 s still fails by one second). Cost, measured on the 204,045-event jittered stream (table below): a larger watermark delays every window result by about the watermark, and longer de-dup retention and open windows hold more state. In Spark the two knobs are tied (dedup state follows the watermark): with a 10 s watermark Spark removed the duplicate itself but still dropped e6 (window [0,60) = 57.5), and with a 60 s watermark Spark equalled the batch result \u2013 confirming that lateness, not the engine, is the root cause, and that one setting must carry both responsibilities there.")
rp.h2("2.3 Engineering comparison (not execution time alone)")
c = t2["compare"]
rp.table([["Metric", "A: batch", "B: stream (watermark 10 s)"],
          ["Throughput (events/s, n=3)", "%s \u00b1 %s" % ("{:,.0f}".format(c["batch_rate"]), "{:,.0f}".format(c["batch_rate_sd"])), "%s \u00b1 %s" % ("{:,.0f}".format(c["stream_rate"]), "{:,.0f}".format(c["stream_rate_sd"]))],
          ["End-to-end latency window end \u2192 result", "%s s (results exist only after the whole job)" % "{:,.0f}".format(c["lat_batch_mean"]), "%.2f s mean, %.2f s p95" % (c["lat_stream_mean"], c["lat_stream_p95"])],
          ["State / memory held", "{:,} event IDs plus all events".format(c["state_batch"]), "{:,} entries (peak windows + IDs)".format(c["state_stream"])],
          ["Result correctness vs batch", "reference", "%d of %d windows exact; mean error %.3f, max %.3f km/h" % (c["windows"] - c["wrong_windows"], c["windows"], c["mae"], c["maxerr"])],
          ["Late events dropped", "0", "{:,} (0.39%)".format(c["late_dropped"])],
          ["After a restart", "re-reads all {:,} stored events; deterministic".format(c["n_events"]), "with %d KB checkpoint: 0 windows differ; **stateless restart: %d windows wrong**" % (c["snapshot_kb"], c["restart_nostate_bad"])]],
         [1.8, 2.1, 2.37], "Measured comparison on 204,045 delivered events (200,000 unique, 4,045 duplicates; 5% of events delayed with mean 12 s)")
rp.p("Interpretation: batch is faster per event and exactly right but its latency is the length of the whole data collection (about 5,035 s on average here); streaming delivers each window about 10.7 s after it ends, holds 140\u00d7 less state (1,430 vs 200,000 entries) and is correct only to within the lateness it tolerates; its correctness after a crash depends entirely on checkpointing the window and de-dup state.")
rp.h2("2.4 Changed requirement \u2013 \u201cAlerts within two seconds; a few late events may be ignored\u201d")
rows = [["Watermark", "Late events dropped", "% dropped", "Windows differing", "Mean latency s", "Results \u2264 2 s", "Peak state"]] + [["%d s" % s["L"], "{:,}".format(s["dropped"]), "%.2f%%" % s["pct"], "%d / %d" % (s["wrong"], s["windows"]), "%.2f" % s["mean_lat"], "%.1f%%" % s["within2"], s["state"]] for s in t2["sweep"]]
rp.table(rows, [0.8, 1.0, 0.8, 1.05, 0.9, 0.9, 0.82], "Watermark sweep on the same 204,045 events", align_right_from=1)
rp.image(FG("fig_task2.png"), "Task 2: (a) the counterexample, (b) latency vs watermark against the 2 s limit, (c) correctness vs state", 6.27)
rp.p("**Conclusion from the measurements.** In append mode the result of a window appears only when the watermark passes its end, so latency \u2248 watermark + arrival delay: a 1 s watermark gives a mean of 1.82 s (99.4% of windows within 2 s), whereas a 2 s watermark already gives 2.79 s and **0% within 2 s**. The 2-second requirement therefore forces a watermark of at most 1 s, and at that setting 0.92% of events are dropped (1.64% at 0 s) \u2013 acceptable under \u201ca small number of late events may be ignored\u201d, but the per-window averages are inexact for most windows because each window contains about 150 events and losing any one changes the mean (mean error stayed below 1 km/h in the 10 s run). Batch cannot meet the requirement at all. The alert path should be **event-level (update mode)**: evaluating each event as it arrives reaches the engine within 2 s for 94.4% of events; the remaining 5.6% are the delayed tail, which can only be fixed by a later correction or batch re-computation. Choice: streaming, event-time windows, watermark \u2264 1 s, early/updated results per event, and a periodic batch job to reconcile.")
rp.h2("Boundary / failure tests and intermediate evidence")
rp.p("Boundary cases built into the counterexample: out-of-order but within watermark (e5, kept correctly), late beyond watermark (e6), duplicate after de-dup eviction (e2 copy), plus the exact-boundary test that watermark 41 s works and 40 s fails. Restart tests: checkpoint restore reproduced the uninterrupted result exactly (0 differing windows) and a stateless restart corrupted 672 of 1,336 windows.")
consoles(2, "Task 2")

# ============================================================ TASK 3
rp.page_break(); rp.h1("TASK 3 \u2013 Security and Privacy Engineering Under Attack (10 Marks)")
rp.h2("Configuration, source code and test data")
rp.p("All data is synthetic. **task3/data.py** creates 5,000 beneficiaries (Name, ID_Number, PIN_Code, Date_of_Birth, Gender, Scheme, Amount) and a **public auxiliary dataset** (Name, PIN_Code, Date_of_Birth, Gender) covering a random 60% (3,000) of the same people. The design makes the attack meaningful: 25 PIN codes \u00d7 14,610 possible birth dates \u00d7 2 genders = 730,500 combinations for 5,000 people, so most people are unique on (PIN, DOB, Gender). Amounts depend on scheme, region and age so that utility loss is measurable.")
rp.image(SS("task3_code.png"), "Core of task3/access.py \u2013 role gatekeeper and hash-chained audit log", 5.4)
rp.h2("Stage A \u2013 normal access control")
rp.p("Two roles are implemented with SQLite **views**: the **fraud analyst** reads v_analyst (all fields including Name and ID_Number); the **researcher** reads v_researcher (Name and ID_Number dropped \u2013 the Part I Task 4 rule). A gatekeeper function allows a role to read only its own view and writes an **audit entry for every attempt, allowed or denied**. Each entry stores SHA-256(previous hash + entry), forming a hash chain. The console output shows the rows each role sees, the three audit entries (analyst ALLOWED, researcher ALLOWED, researcher DENIED when it tried to read the base table), and the chain verification (VALID).")
rp.h2("Stage B \u2013 linkage attack")
B = t3["B"]; pr = B["pred"]
rp.table([["Quantity", "Prediction (made before the attack)", "Observed"],
          ["Combinations (cells)", "{:,}".format(pr["cells"]), "{:,}".format(pr["cells"])], ["P(record unique) = exp(\u2212(N\u22121)/cells)", "%.4f" % pr["p_unique"], "%.4f" % (B["unique"] / 5000)],
          ["Released records unique on (PIN, DOB, Gender)", "%.0f" % pr["unique_records"], "{:,}".format(B["unique"])], ["Records re-identified by joining the auxiliary data", "%.0f (60%% of unique)" % pr["reidentified"], "{:,} (error +0.1%)".format(B["reidentified"])],
          ["Of these, correct (checked against ground truth)", "\u2013", "{:,} (precision 100%)".format(B["correct"])]], [2.9, 1.9, 1.47], "Stage B \u2013 prediction vs attack result")
rp.p("**Interpretation.** Removing Name and ID_Number does not anonymise the data: **2,983 of 5,000 people (59.7%) had their Name linked to Scheme and Amount** using nothing more than PIN code, date of birth and gender. The probabilistic prediction was accurate to 0.1% because the quasi-identifier space is huge relative to the population.")
rp.h2("Stage C \u2013 repair and measure")
C = t3["C"]; lat = C["lattice"]
digs = {6: "6 digits", 5: "5 digits", 4: "4 digits", 3: "3 digits", 0: "none"}; lv = ["exact", "month", "year", "5-yr band", "10-yr band", "20-yr band"]
rows = [["PIN kept \\ DOB"] + lv]
for pdig in (6, 5, 4, 3, 0):
    rows.append([digs[pdig]] + [("k=%d" % x["k"]) + (" (%.1f%%)" % (100 * x["supp"]) if x["supp"] else "") for x in lat if x["pin"] == pdig])
rp.table(rows, [1.05, 0.8, 0.8, 0.85, 0.95, 0.9, 0.92], "Generalisation lattice: minimum class size k (percentage = records in classes smaller than 5 that must be suppressed)")
rp.table([["Measure", "Before (original rule)", "After (PIN 6 digits + 5-year birth band, 6 records suppressed)"],
          ["k-anonymity achieved", "1", "**k = %d**" % C["k"]], ["Records still re-identifiable", "{:,}".format(B["reidentified"]), "**%d**" % C["reid_after"]], ["Records suppressed", "0", "%d of 5,000 (0.12%%)" % C["suppressed"]],
          ["Mean Amount per birth year (utility)", "exact", "mean absolute error %.2f%% (only band means available)" % C["mape_age"]], ["Overall mean Amount", "%.2f" % C["glob_before"], "%.2f (\u22120.03%%)" % C["glob_after"]], ["Information-loss index (0\u20131)", "0", "%.3f" % C["best"]["loss"]]],
         [2.0, 1.5, 2.77], "Stage C \u2013 chosen release (minimum information loss with at most 2% suppression)")
rp.p("**Trade-off.** Generalising only the PIN is not enough (k stays 1 even with the PIN fully suppressed while the exact date of birth remains), and generalising only the date of birth to a 5-year band gives k = 2 with an almost unchanged PIN. The cheapest lattice node meeting k \u2265 5 keeps the full PIN and replaces the birth date by a 5-year band, suppressing 6 outlying records. A higher level of protection costs more: k = 16 needs a 10-year band (loss index 0.125, twice as much). The analytical price at the chosen node is a 3.54% error when answering \u201cmean Amount per single birth year\u201d, while totals by scheme or overall barely change (below 0.1%). k-anonymity limits **identity** disclosure only; it does not stop attribute disclosure if everybody in a class has the same Scheme.")
rp.h2("Stage D \u2013 encryption and integrity")
D = t3["D"]
rp.table([["Pipeline run (100,000 records, mean \u00b1 SD of 3)", "Plaintext", "ID_Number and Amount encrypted (AES-256-GCM) + HMAC"],
          ["Run time (read file, decrypt Amount, mean Amount per Scheme)", "%.3f \u00b1 %.3f s" % (D["plain_mean"], D["plain_sd"]), "%.3f \u00b1 %.3f s  (**%+.0f%%**)" % (D["enc_mean"], D["enc_sd"], D["overhead_pct"])],
          ["File size", "%.1f MB" % (D["size_plain"] / 1e6), "%.1f MB  (+%.0f%%: nonce, tag, Base64, MAC column)" % (D["size_enc"] / 1e6, 100 * (D["size_enc"] / D["size_plain"] - 1))],
          ["One-off protect-and-write cost", "\u2013", "%.2f s" % D["protect_s"]], ["Aggregate result identical", "\u2013", "yes"]], [2.6, 1.3, 2.37], "Encryption overhead")
rows = [["Deliberate alteration (20,000 protected records)", "Per-record HMAC", "AES-GCM tag", "File SHA-256", "Record count"]]
for t in D["tamper"]:
    rows.append([t["attack"], "FAIL (%d)" % t["hmac"] if t["hmac"] else "not detected", "FAIL (%d)" % t["gcm"] if t["gcm"] else "not detected", "changed" if t["file_hash"] else "same", "changed" if t["count"] else "same"])
rows.append(["T5 edit audit entry #1 (rows 3 \u2192 0)", "\u2013", "\u2013", "\u2013", "hash chain broken at seq 1"])
rp.table(rows, [2.6, 0.9, 0.9, 0.9, 0.97], "Tamper-detection demonstration")
rp.p("**What each control does not protect against.**")
rp.table([["Control", "Does NOT protect against"],
          ["Role views / masking", "Authorised misuse, a database administrator who bypasses the views, and inference: Stage B showed the researcher view alone leaks identities."],
          ["Hash-chained audit log", "Reading itself (it only records it); deletion of the newest entries unless the latest hash is stored elsewhere; a writer who recomputes the whole chain."],
          ["Generalisation (k-anonymity)", "Attribute disclosure when a class is homogeneous, linking of several releases, and richer auxiliary data."],
          ["AES-256-GCM on fields", "Key theft, data after decryption in memory, unencrypted fields (PIN, DOB remain readable), access-pattern leakage, and deletion of whole rows."],
          ["Per-record HMAC", "Deletion, reordering or replay of whole valid records (T4 above was not detected by it) and anyone holding the MAC key."],
          ["File SHA-256 / record count", "An attacker who can also rewrite the stored hash; it detects that something changed but not who or what."]], [1.7, 4.57], "Limits of each control")
rp.image(FG("fig_task3.png"), "Task 3: (a) k-anonymity lattice, (b) privacy vs utility trade-off, (c) encryption overhead", 6.27)
rp.h2("Boundary / failure tests")
rp.p("Failure cases demonstrated: a researcher requesting the base table is denied and the denial is audited; five tamper experiments (edit of a plaintext field, ciphertext modification, swap of two encrypted values, deletion of a whole record, edit of an audit entry); the deletion case is the one that per-record controls miss and only the file hash and record count catch; the lattice shows the boundary where suppression exceeds 2% and a node is rejected.")
consoles(3, "Task 3")

# ============================================================ TASK 4
rp.page_break(); rp.h1("TASK 4 \u2013 Data Quality Engineering (7 Marks)")
rp.h2("4.1 Cleaning stage \u2013 configuration, source code, test data")
rp.p("task4/cleaning.py applies five ordered rules to every raw line of the feed (sensor_id, segment, speed, event_time): **R1** field count must be 4; **R2** no missing value; **R3** speed must be numeric (a unit suffix such as \u201c55.1 km/h\u201d is **repaired**; text such as \u201cfast\u201d is rejected) and the timestamp must parse; **R4** speed within [0, 200]; **R5** duplicates on (sensor, time) \u2013 the first copy is kept, the others are quarantined. Rejected lines go to data/quarantine.csv with line number, rule, reason and raw text; accepted lines go to data/clean.csv. The test feed (task4/feed.py, seed 3) has 200,000 distinct events with about 1% malformed, 1.5% missing speed, 0.5% missing sensor, 1% out-of-range, 1% non-numeric, 1% repairable and 1% bad-timestamp records, plus 5% re-sent duplicates (210,526 lines).")
rp.image(SS("task4_code.png"), "Core of task4/cleaning.py \u2013 the rule engine", 5.8)
r4 = t4["rules"]
rp.h2("4.2 Decisions and per-rule summary")
rp.table([["Rule", "Decision", "Records", "Share of lines read"]] + [[k, d, "{:,}".format(r4[k]), "%.2f%%" % (100 * r4[k] / t4["read"])] for k, d in (("R1_FIELD_COUNT", "reject"), ("R2_MISSING_VALUE", "reject"), ("R3_TYPE_REPAIR_OR_REJECT", "repair / reject"), ("R4_RANGE", "reject"), ("R5_DUPLICATE", "reject (keep first)"))] +
         [["KEEP (unchanged)", "keep", "{:,}".format(t4["keep"]), "%.2f%%" % (100 * t4["keep"] / t4["read"])], ["REPAIR (unit suffix stripped)", "repair", "{:,}".format(t4["repair"]), "%.2f%%" % (100 * t4["repair"] / t4["read"])], ["Total (reconciles with 210,526 lines read)", "", "{:,}".format(t4["read"]), "100.00%"]],
         [2.3, 1.3, 1.1, 1.57], "Per-rule summary", align_right_from=2)
rows = [["Line", "Decision", "Rule that fired", "Why"]] + [[str(t[0]), t[1], t[2], t[3]] for t in t4["trace"][:10]]
rp.table(rows, [0.6, 0.8, 1.9, 2.97], "Decision trace for a sample of records")
rp.h2("4.3 Predict before you execute \u2013 duplicates from 5% to 40%")
dp = t4["dup"]; a, b = dp["obs"]["0.05"], dp["obs"]["0.4"]
rp.table([["", "Prediction (saved before the run)", "Observed at 5%", "Observed at 40%", "Observed ratio"],
          ["Records kept", "unchanged (%s)" % "{:,}".format(dp["pred"]["kept"]), "{:,}".format(a["kept"]), "{:,}".format(b["kept"]), "\u00d7%.2f" % (b["kept"] / a["kept"])],
          ["Run time", "\u00d7%.2f" % dp["pred"]["time_ratio"], "%.3f \u00b1 %.3f s" % (a["mean"], a["sd"]), "%.3f \u00b1 %.3f s" % (b["mean"], b["sd"]), "\u00d7%.2f" % (b["mean"] / a["mean"])],
          ["Shuffle volume (records / KB)", "\u00d7%.2f" % dp["pred"]["shuffle_ratio"], "{:,} / {:,.0f}".format(a["shuffle_records"], a["shuffle_bytes"] / 1e3), "{:,} / {:,.0f}".format(b["shuffle_records"], b["shuffle_bytes"] / 1e3), "\u00d7%.2f" % (b["shuffle_bytes"] / a["shuffle_bytes"])]],
         [1.4, 1.35, 1.2, 1.3, 1.02], "Task 4.3 \u2013 prediction and observation")
rp.p("**Comparison.** Records kept (identical) and shuffle volume (\u00d71.58 for both records and bytes) were predicted correctly: duplicates add nothing to the output and the volume sent to the de-duplication stage grows with the delivered lines. **The run-time prediction was wrong (\u00d71.58 predicted, \u00d71.99 observed)** because it assumed every line costs the same; in fact a rejected duplicate triggers extra work (building a quarantine record with its reason and raw text, 125,244 of them at 40% against 9,879 at 5%), so cost grows faster than the line count. Lesson: quarantine volume, not only input volume, drives the cost of a cleaning stage.")
rp.h2("4.4 Schema drift challenge")
d4 = t4["drift"]
rp.table([["Pipeline variant (50,000 lines)", "Kept", "Rejected", "Mean speed"], ["Baseline feed (km/h, 4 fields)", "46,893", "3,107", "%.2f" % d4["base_mean"]], ["Drifted feed, strict schema (R1 on)", "0", "50,000", "n/a"], ["Drifted feed, tolerant of extra fields", "50,000", "0", "%.2f" % d4["tolerant_mean"]],
          ["Tolerant + unit conversion (\u00d73.6) after monitor alert", "50,000", "0", "%.2f" % d4["converted_mean"]]], [3.0, 0.9, 0.9, 1.47], "Effect of the source changing km/h \u2192 m/s and adding a field", align_right_from=1)
rp.p("**Does the pipeline detect it?** The **new field** is detected immediately by R1 (all 50,000 lines rejected \u2013 loud but the whole feed is lost). The **unit change** is **not** detected by any record-level rule: m/s values (0\u201355) all lie inside [0, 200], so if the pipeline is relaxed to accept extra fields it silently produces a mean speed of %.2f instead of %.2f km/h (\u00d70.28) \u2013 every congestion report would be wrong. **Detection:** a batch-level monitor compares the median speed with a trusted baseline; the ratio %.3f matches 1/3.6 = 0.278, which flags a unit change rather than ordinary variation. **Handling:** a schema registry records the unit per source version; on an alert the batch is held, the conversion \u00d73.6 is applied only after a human or a registry update confirms the unit, and the result returns to %.2f km/h (0.03%% from baseline)." % (d4["tolerant_mean"], d4["base_mean"], d4["ratio"], d4["converted_mean"]))
rp.image(FG("fig_task4.png"), "Task 4: (a) records per rule, (b) duplicate experiment, (c) schema drift effect", 6.27)
rp.h2("4.5 Engineering extension \u2013 ten more sources with different formats (not implemented)")
rp.bullets(["**Validation design.** Introduce one small adapter per source that parses its format into a single canonical record and one versioned **schema contract** per source (field names, types, units, time zone). Record-level rules then apply to the canonical model; source-specific rules sit in the adapter. Units and time zones are normalised at the adapter, because Task 4.4 showed range rules cannot see a unit change.",
            "**Rule management.** Hard-coded rules do not scale to ten owners: rules become configuration (id, owner, version, severity, action keep/repair/reject), stored in version control, each with golden test records and a regression run before release; rule order and precedence are explicit, and every change is reviewed because it changes what data is trusted.",
            "**Quarantine.** Partition quarantine by source and rule with standard reason codes, retention and access limits (it holds raw, possibly personal, data), and provide a **replay** path so quarantined records can be re-processed after a rule or adapter fix instead of being lost.",
            "**Monitoring.** Per-source dashboards for volume, freshness, rejection rate per rule, null rate and distribution (median/quantiles) against baselines, with alerts on sudden jumps: in this report a 100% R1 rejection and a 0.278 median ratio are the signals that caught the two drift effects. Cost grows with sources, so sampling and thresholds per source are needed."])
consoles(4, "Task 4")

# ============================================================ TASK 5
rp.page_break(); rp.h1("TASK 5 \u2013 Three Storage Models, One Dataset (7 Marks)")
rp.h2("Configuration, source code and test data")
rp.p("One generator (task5/stores.py) wrote **5,000,010 traffic events** (500 sensors, 30 days, about 166,667 events/day) into three stores in a single pass: (1) a **row-oriented CSV** file in arrival order; (2) **Parquet** (PyArrow, zstd, 60 row groups of at most 100,000 rows, **sorted by date then sensor** so min/max statistics prune well); (3) a **relational SQLite** table with an index on (sensor_id, event_date). Bytes read are measured as the change in the process\u2019s read-byte counter (/proc/self/io rchar). Each query ran once after dropping the page cache (cold) and three more times (warm, mean \u00b1 SD).")
rp.image(SS("task5_code.png"), "Core of task5/stores.py \u2013 Q1 and Q2 on each store", 6.2)
rp.h2("Expected behaviour (predictions recorded before any query)")
rp.p("Q1 point lookup: CSV ~100% of the file, Parquet ~1% (row-group pruning), SQLite ~1% (index seek). Q2 week scan: CSV ~100%, Parquet ~8% (7 of 30 days, 2 of 5 columns), SQLite ~100% (the index is on sensor, not date). Q1\u2032 (10 sensors): bytes \u00d71 CSV, \u00d72 Parquet, \u00d73 SQLite. Q2\u2032 (one column): bytes \u00d71 CSV, \u00d70.6 Parquet, \u00d71 SQLite.")
rp.h2("Actual output: size, data read, run time, tuning")
sz = t5["sizes"]; q = t5["queries"]
rows = [["Query", "Store", "Cold s", "Warm s (n=3)", "Bytes read", "% of store", "Rows / groups"]]
store_mb = {"CSV": sz["CSV"], "Parquet": sz["Parquet"], "SQLite": sz["SQLite"]}
db_bytes = {"CSV": 244991053, "Parquet": 27.9e6, "SQLite": 429.0e6}
for qq in ("Q1", "Q2"):
    for st in ("CSV", "Parquet", "SQLite"):
        v = q["%s|%s" % (qq, st)]; rows.append([qq, st, "%.3f" % v["cold"], "%.3f \u00b1 %.3f" % (v["warm_mean"], v["warm_sd"]), "{:,.0f}".format(v["bytes"]), "%.1f%%" % (100 * v["bytes"] / (store_mb[st] * 1e6)), v["result"]])
rp.table(rows, [0.5, 0.75, 0.7, 1.25, 1.2, 0.8, 1.07], "Q1 (sensor S0123 on 2026-03-10) and Q2 (average speed per segment, 2026-03-08 to 2026-03-14)", align_right_from=2)
tu = t5["tuning"]; w3 = t5["Q3"]
rp.table([["Measure", "CSV", "Parquet", "SQLite"], ["Storage size", "%.1f MB" % sz["CSV"], "%.1f MB (8.8\u00d7 smaller)" % sz["Parquet"], "%.1f MB (+%.1f MB after covering index)" % (tu["db_mb_before"], tu["db_mb_after"] - tu["db_mb_before"])],
          ["Tuning needed", "none (and none possible)", "sort by (date, sensor), 100k-row groups, zstd", "index (sensor_id, event_date); covering index (event_date, segment, speed) cut Q2 from 0.687 s to 0.295 s"],
          ["Build time", "%.1f s" % t5["build"]["csv_s"], "%.1f s" % t5["build"]["parquet_s"], "%.1f s insert + %.1f s index" % (t5["build"]["sqlite_insert_s"], t5["build"]["sqlite_index_s"])],
          ["Q3: 50 batches \u00d7 1,000 events (n=3)", "%.3f \u00b1 %.3f s = {:,.0f} ev/s".format(w3["CSV"]["eps"]) % (w3["CSV"]["mean"], w3["CSV"]["sd"]), "%.3f \u00b1 %.3f s = {:,.0f} ev/s; 50 new files per run".format(w3["Parquet"]["eps"]) % (w3["Parquet"]["mean"], w3["Parquet"]["sd"]), "%.3f \u00b1 %.3f s = {:,.0f} ev/s; 50 commits".format(w3["SQLite"]["eps"]) % (w3["SQLite"]["mean"], w3["SQLite"]["sd"])]],
         [1.45, 1.2, 1.7, 1.92], "Size, tuning and write load")
rp.image(FG("fig_task5.png"), "Task 5: (a) query time, (b) data read per query, (c) storage size", 6.27)
rp.p("**Why each model behaves as observed.** **CSV** is row-oriented text with no statistics or index, so every query reads all 245 MB (100%) even to return 352 rows; Q1 and Q2 take 2.9 s and 1.8 s and only the parsing differs. **Parquet** is columnar and compressed (dictionary + zstd: 27.9 MB), and because the file is sorted by (date, sensor) each row group has a narrow min/max range: Q1 read 2.2% of the file (0.014 s) and Q2 read 5.7% (0.134 s) \u2013 the prediction of about 1% and 8% was in the right range. **SQLite** stores rows in B-tree pages: Q1 uses the index and touches 0.3% of the database (0.001 s), but Q2 filters on a date range the index cannot serve, so it scans 80.5% of the database (0.687 s) until a covering index is added, at the price of 172 MB more storage and slower writes. Writes: CSV append and Parquet batch files are append-only (about 840,000 events/s), SQLite must maintain two indexes under transactions (about 31,000 events/s; it also wrote 721 MB per run, which includes the WAL switch and checkpoint of a 600 MB database \u2013 I did not isolate that further).")
rp.h2("Stress the design \u2013 changed query patterns")
def ratio(a, b): return b / a
rows = [["Store", "Q1\u2032 time \u00d7 / bytes \u00d7 (pred bytes \u00d7)", "Q2\u2032 time \u00d7 / bytes \u00d7 (pred bytes \u00d7)", "Explanation of the result"]]
pp = t5["pred"]
expl = {"CSV": "As predicted: still a full scan; one-column parsing saves 21% time but not a single byte read.",
        "Parquet": "Both predictions too pessimistic: the 10 sensors are contiguous inside the row groups already read, and the segment column is a tiny dictionary column, so dropping it saves no bytes (but 69% of time).",
        "SQLite": "Prediction wrong: BETWEEN on the first index column makes event_date a post-filter, so all 30 days of 10 sensors are read (\u00d7394 bytes). Q2\u2032 was fast only because the covering index added in the tuning step already existed."}
for st in ("CSV", "Parquet", "SQLite"):
    a1, b1, c1, d1 = q["Q1|%s" % st], q["Q1'|%s" % st], q["Q2|%s" % st], q["Q2'|%s" % st]
    rows.append([st, "\u00d7%.2f / \u00d7%.2f (\u00d7%.1f)" % (b1["warm_mean"] / a1["warm_mean"], b1["bytes"] / a1["bytes"], pp["Q1p_vs_Q1_bytes"][st]), "\u00d7%.2f / \u00d7%.2f (\u00d7%.1f)" % (d1["warm_mean"] / c1["warm_mean"], d1["bytes"] / c1["bytes"], pp["Q2p_vs_Q2_bytes"][st]), expl[st]])
rp.table(rows, [0.7, 1.45, 1.45, 2.67], "Predicted vs measured effect of changing the query pattern (Q1\u2032: 10 sensors; Q2\u2032: AVG(speed) only)")
rp.h2("Industry decision")
rp.table([["Environment", "What matters", "Evidence from this dataset", "Choice"],
          ["A. Transactional lookup service", "Low-latency point reads and updates; selective index", "SQLite Q1: 0.001 s, 0.3% of bytes; Parquet 0.014 s; CSV 2.9 s (full scan). But index design matters: Q1\u2032 range query read \u00d7394 more bytes.", "Indexed row store (relational / key-value) with the index column order matched to the query"],
          ["B. Historical analytics warehouse", "Scan large ranges of few columns; compression; immutable data", "Parquet is 8.8\u00d7 smaller than CSV, Q2 in 0.134 s reading 5.7% vs 0.687 s / 80.5% in SQLite and 1.78 s / 100% in CSV; layout (sorted by date, sensor) is what enabled pruning.", "Columnar format, partitioned and sorted on the common filters"],
          ["C. High-rate sensor ingestion", "Sustained append rate, no write amplification, durability", "Append-only CSV / Parquet batches: ~840,000 events/s vs SQLite ~31,000 events/s (index maintenance, 50 commits). Parquet creates one immutable file per batch (150 files after three runs) \u2013 the small-file problem.", "Append-only log or partitioned files with periodic compaction into Parquet (or an LSM-tree store), queried by the warehouse"]],
         [1.2, 1.4, 2.4, 1.27], "Which storage characteristics matter in three environments")
consoles(5, "Task 5")

# ============================================================ TASK 6
rp.page_break(); rp.h1("TASK 6 \u2013 Fraud-Link Detection at Scale (9 Marks)")
rp.h2("6.1 Model the problem")
rp.table([["Element", "Definition"], ["Input", "A stream or file of payment events (account, day, beneficiary)"], ["Output", "The set of flagged accounts, with the beneficiaries and days that justify each flag"],
          ["Objective", "Flag an account if, in some 7-day window (days d to d+6), it paid **3 or more distinct beneficiaries** (Rule A)"], ["Constraints", "Exact result for stored data; events of one account may arrive in any order; cost must grow slowly with the number of events; personal data (account) must not leave its region (Task 6.6)"]],
         [1.2, 5.07], "Problem model")
rp.p("**Why the current event alone is insufficient:** whether the third distinct beneficiary has been reached depends on the earlier payments of the same account in the last seven days. The pair (account, current beneficiary) says nothing about how many different beneficiaries were paid recently, so each account must keep its **recent history**: the (day, beneficiary) pairs of the last 7 days, or equivalently the set of beneficiaries with their latest payment day.")
rp.h2("6.2 State and methods")
rp.p("**Keyed method (state per account).** Per account keep a queue of (day, beneficiary) events in day order and a counter beneficiary \u2192 number of events in the queue. **New event:** append (day, beneficiary) and increment its counter. **Expiry:** while the oldest day is at least 7 days before the new day, pop it and decrement (delete when the counter reaches 0). **Flag:** if the counter has \u2265 3 keys, flag the account. This is correct because any qualifying window [d, d+6] ends at its last event e, and the window [e\u22126, e] contains it. Events are first sorted by (account, day), which also gives the grouping. **Naive method.** For every event take its day as a window start and compare it with every other event: collect beneficiaries of events of the same account within days d to d+6 and flag the account if at least 3 distinct ones exist \u2013 about n\u00b2 comparisons and no state.")
rp.image(SS("task6_code.png"), "Core of task6/detector.py \u2013 naive and keyed methods", 5.0)
rp.h2("6.3 Implementation and test on the Part I events")
rp.p("**Assumption:** the eight events of Part I Task 6 were not provided to the author; eight placeholder events following the same rule are stored in tests/part1_events.json (A1 pays B1, B2, B3 on days 1, 2, 5 \u2013 flagged; A2 pays only B1; A3 pays B1, B2, B3 on days 1, 5, 9 \u2013 never three distinct within seven days). Replace the file with the real events and re-run. Both methods flag A1 and the program prints the beneficiaries and days: window days 1..7, events (1, B1), (2, B2), (5, B3).")
rp.h2("6.4 Validation by hand (20 events)")
rp.table([["Account", "Events (day, beneficiary)", "Hand reasoning", "Flag?"], ["X", "(1,b1) (3,b2) (7,b3)", "window days 1\u20137 contains b1, b2, b3; day 7 = d+6 is inside", "yes"], ["Y", "(1,b1) (3,b2) (8,b3)", "[1..7] = {b1,b2}; [3..9] = {b2,b3}; day 8 is 7 days after day 1", "no"],
          ["Z", "(2,b1) \u00d74", "four payments but 1 distinct beneficiary", "no"], ["P", "(1,b1) (2,b2) (3,b2) (4,b3)", "b1, b2, b3 all within days 1\u20134", "yes"], ["Q", "(10,b1) (12,b2) (20,b3)", "never 3 within seven days", "no"], ["S", "(3,b1) (3,b2) (3,b3)", "three beneficiaries on the same day", "yes"]],
         [0.7, 1.9, 3.1, 0.57], "Hand-derived expected result for the 20-event instance: flagged = {X, P, S}")
t6h = t6["hand"]
rp.p("The naive method returned %s, the keyed method %s, and the hand result is %s: **all three agree**. **What this validation gives:** the window boundary (day 7 inside, day 8 outside), repeated payments to one beneficiary and same-day payments are handled correctly, and the two methods agree on a case a human can verify; the larger runs (naive = keyed at 1,000 to 10,000 events) extend that agreement. **What it cannot detect:** performance problems, behaviour with out-of-order or enormous accounts, errors that the hand analysis shares with the code (a wrong reading of the rule), and rare cases not in the 20 events." % (t6h["naive"], t6h["keyed"], t6h["hand"]))
rp.h2("6.5 Investigate growth")
tab = t6["table"]; kv = t6["keyed"]; sl = t6["slope"]
rows = [["Events", "Method", "Comparisons / records processed", "Run time", "Memory / shuffle observation"]]
for t in tab:
    n = t["n"]
    rows.append(["{:,}".format(n), "naive", "\u2248 n\u00b2 = %.0e pairs" % (n * n), ("%.2f s (measured)" % t["naive"]) if t["naive_measured"] else ("%.3g s = %.3g h (extrapolated, n^%.2f)" % (t["naive"], t["naive"] / 3600, sl)), "no state; no grouping, so no shuffle but all events must be visible to every comparison"])
    rows.append(["", "keyed", "n = {:,} events + sort".format(n), "%.2f s (measured, %d run%s)" % (kv[str(n)]["mean"], kv[str(n)]["runs"], "s" if kv[str(n)]["runs"] > 1 else ""), "peak RSS %.0f MB%s" % (kv[str(n)]["rss"], " (interpreter baseline dominates)" if n < 10_000_000 else " (arrays + sorted copies)")])
rp.table(rows, [0.8, 0.6, 1.5, 1.7, 1.67], "Growth table (naive measured up to 10,000 events, beyond that extrapolated from a fitted power law; keyed measured at every size)")
rp.p("The naive timings at 1,000 / 2,000 / 5,000 / 10,000 events were 0.017 s, 0.065 s, 0.592 s and 2.09 s, a fitted growth of **n^%.2f** (quadratic is 2): %s." % (sl, "100\u00d7 more events cost roughly 10,000\u00d7 more time"))
rp.callout("Inquiry \u2013 why does grouping remove work, yet cost still grows?", "Grouping by account turns \u201ccompare every event with every other event\u201d into \u201ccompare each event with the few recent events of its own account\u201d: 10,000,000 events took 11.0 s instead of a projected 1,630 hours. What remains is (1) the sort/shuffle that brings an account\u2019s events together, which still grows as n log n and is the part that crosses the network on a cluster; (2) **state**: the queue holds every event inside the window; (3) **skew** \u2013 the work and state of one account are indivisible. The skew test below shows (2) and (3).")
sk6 = t6["skew"]
rp.table([["Test (1,000,000 events)", "Run time", "Largest per-account window state", "Events in the busiest of 8 hash partitions (max / mean)"],
          ["Uniform accounts", "%.3f s" % sk6["uniform"]["seconds"], "%d events / %d beneficiaries" % (sk6["uniform"]["max_deque"], sk6["uniform"]["max_distinct"]), "%s (1.01)" % "{:,}".format(max(sk6["uniform"]["partitions"]))],
          ["One hot account with 50% of events", "%.3f s" % sk6["hot account 50%"]["seconds"], "%s events / %d beneficiaries" % ("{:,}".format(sk6["hot account 50%"]["max_deque"]), sk6["hot account 50%"]["max_distinct"]), "%s (4.50)" % "{:,}".format(max(sk6["hot account 50%"]["partitions"]))]],
         [1.8, 0.9, 1.7, 1.87], "Skew experiment")
rp.p("On one core the run time barely changed, but the hot account\u2019s window state grew from 6 events to 9,851 events, and in a distributed setting the partition holding it receives **563,011 of 1,000,000 events (56%)**, so all other machines wait for that one. The distinct-beneficiary counter stayed at 50 entries: the *useful* state is small, the *stored* state (every event) is not.")
rp.image(FG("fig_task6.png"), "Task 6: (a) run time vs events, (b) partition load under skew", 5.6)
rp.h2("6.6 Business requirement change \u2013 one billion events per day, alerts under 5 s, several data centres")
rp.p("**Why the current solution is insufficient.** One billion events per day is about 11,600 events/s on average, and my keyed code processed roughly 900,000 events/s on one core, so raw speed is not the first problem. What breaks is the **shape** of the solution: (1) it is a batch job that sorts **all** events before any flag appears, but alerts are due in under five seconds; (2) the queue keeps every event of the last 7 days, i.e. about 7 \u00d7 10\u2079 events of state, and the hot-account test shows that state and load concentrate on single keys; (3) it assumes all events and accounts are visible in one place, but personal data must stay in its region. The naive method is hopeless (projected 11.8 hours at only one million events). **Property that changed:** from \u201cexact answer over stored data on one machine\u201d to \u201cbounded latency, continuous, geographically distributed, privacy-constrained\u201d.")
rp.p("**Strategy to investigate.** (a) A **streaming, regionally partitioned** design: events are partitioned by account within each region and processed by keyed state (e.g. Spark Structured Streaming or Flink); (b) a **compact per-account state**: a map beneficiary \u2192 latest payment day instead of all events (at most 50 entries in my skew test versus 9,851 events), with entries older than 7 days expired by timers; (c) for extremely active accounts an **approximate distinct counter** (for example HyperLogLog) with bounded memory; (d) only **pseudonymised flags and aggregates** leave the region, never raw account data, and cross-region links are matched on salted hashes. **Trade-off accepted:** a small delay (watermark) and an occasional missed or false flag from late events or approximation, in exchange for bounded latency, bounded memory and data residency \u2013 exactly what management said is acceptable.")
rp.h2("6.7 Technical reflection (150 words or fewer)")
REFL = ("More machines help only when work divides evenly and independently. In my skew test, hashing 1,000,000 events by account onto 8 partitions gave one partition 563,011 events (max/mean 4.50) because one account received half of them; the job ends when that partition does, so eight machines give at most about 1.8\u00d7 speed-up. The naive detector needed 2.09 s at 10,000 events and its fitted n^2.14 growth projects 11.8 hours at 1,000,000, so 100 machines would still need about seven minutes, whereas the keyed algorithm took 1.08 s on one core. In Task 1 the shuffle stayed small only because the combiner cut 3.84 million records to 38,400. Scaling therefore depends on algorithm complexity, data skew and shuffle volume, not on machine count alone.")
assert len(REFL.split()) <= 150, len(REFL.split())
rp.callout("Answer (%d words)." % len(REFL.split()), REFL)
consoles(6, "Task 6")

# ============================================================ rubric map, limits, reproduction
rp.page_break(); rp.h1("3. Rubric Self-Check \u2013 Where Each Criterion Is Evidenced")
rows = [["Task / criterion", "Marks", "Evidence in this report and repository"],
        ["1.1 Implement (records, reducers, single-process comparison)", "3", "Task 1: read / accepted / rejected table, reducer-load table, 10,000-row single-process comparison"],
        ["1.2 Expose behaviour (stages, partitions, shuffle, time)", "2", "Spark stage table, per-stage timings, shuffle with / without combiner, explanation of the dominant map stage"],
        ["1.3 Requirement change (3 sizes, predict first)", "2", "Predictions file saved first; prediction vs observation table at 200k / 1M / 4M rows"],
        ["1.4 Boundary test", "1", "B1\u2013B7 and the chosen skew case B8 with reasons"],
        ["2.1 Normal case", "2", "15 windows side by side, identical"], ["2.2 Break the stream", "3", "StreamResult \u2260 BatchResult, first event (duplicate e2), responsible setting, fix and cost"],
        ["2.3 Engineering comparison", "2", "Latency, throughput, state, correctness, restart table"], ["2.4 Changed requirement", "2", "Watermark sweep with latency and drop rates, conclusion from measurements"],
        ["3 Stage A\u2013D", "10", "Role outputs and audit chain; attack prediction 2,980 vs 2,983; k = 5, 0 re-identifiable, utility loss; encryption +295%, tamper tests, limits table"],
        ["4.1\u20134.5", "7", "Cleaning stage with quarantine and counts, decision trace, prediction vs observation, drift experiment, extension discussion"],
        ["5 Storage models", "7", "Size, data read, time, tuning, Q3, modified queries with predictions, industry decision"],
        ["6.1\u20136.7", "9", "Model, state design, both implementations, hand-checked test, growth table, skew, requirement change, 150-word reflection"]]
rp.table(rows, [2.5, 0.5, 3.27], "Mapping of rubric criteria to evidence")
rp.h1("4. Limitations and Honest Notes")
rp.bullets(["**Platform.** Executed on a single-core, 4 GB machine with Spark in local mode, not on Zoho, Azure or GCP; the shuffle behaviour is genuine but network effects of a real cluster are not measured. Instructions to repeat the runs on a cloud VM or Dataproc are in README.md.",
            "**Streaming source.** Kafka was not available; Spark Structured Streaming read one JSON file per event through its file source, which preserves the engine, watermark and state semantics but not broker behaviour.",
            "**Predictions that were wrong** and are reported as such: Task 4.3 run time (\u00d71.58 vs \u00d71.99), Task 5 Parquet Q1\u2032 / Q2\u2032 byte ratios, SQLite Q1\u2032 (\u00d73 vs \u00d7394), SQLite Q2\u2032 (changed by an earlier tuning step).",
            "**Part I Task 6 events** were not available; placeholders are used (tests/part1_events.json).",
            "**Single runs.** The 4M-row Spark run, the 10,000-event naive run and the 10M-event keyed run were executed once because of their length; all other timings are means of three or more runs.",
            "**Unexplained detail.** The 721 MB written by SQLite per Q3 run is attributed to WAL conversion and checkpointing of a large database but was not isolated experimentally.",
            "**Screenshots.** They are renders of the real console logs in a VS Code layout; run the commands in VS Code to capture native screenshots if the evaluator requires them."])
rp.h1("5. Reproduction and GitHub Upload")
rp.p("Create a virtual environment, install the requirements and run any task; each task writes its console log, JSON results and figure into results/ and figures/.")
rp.table([["Step", "Command"], ["Install", "python -m venv .venv  &&  .venv\\Scripts\\activate  &&  pip install -r requirements.txt   (Java 17+ is needed for Spark)"], ["Run one task", "python run_task1.py   (likewise run_task2.py \u2026 run_task6.py)"], ["Run everything", "bash run_all.sh   (about 25 minutes on one core; Task 5 needs about 1.2 GB of free disk)"],
          ["Create the repository", "git init  &&  git add .  &&  git commit -m \"CO4 Part II big data engineering\""], ["Publish", "git branch -M main  &&  git remote add origin https://github.com/<user>/CO4_BigData_Assignment.git  &&  git push -u origin main"]],
         [1.5, 4.77], "Commands")
rp.h1("6. Conclusion")
rp.p("The six investigations show one pattern: **big-data systems are governed by data layout, shuffle volume, state and skew, not by raw speed alone.** The combiner made the batch pipeline scale; the watermark and de-duplication retention, not the engine, decided whether streaming matched batch; removing identifiers did not anonymise data, while a carefully chosen generalisation did at a measured utility cost; cleaning rules cannot see a silent unit change without distribution monitoring; sorted columnar layout beat both text and a row store for scans while an index won point lookups; and the keyed algorithm removed the quadratic work but left state and skew as the next limits. Every claim above is backed by a run whose log is included.")
doc.save(OUT); print("saved", OUT)
