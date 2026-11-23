# CO4 - Big Data Engineering: Implement, Test, Secure & Scale (Assignment 4, Part II)

Six tasks, one script each. Every script prints the evidence (predictions, actual output, boundary tests) and saves
JSON results to `results/`, charts to `figures/`. Predictions are saved to `results/task*_prediction*.json` **before** the runs they test.

| Task | Script | What it demonstrates |
|---|---|---|
| 1 | `run_task1.py` | Map/shuffle/reduce + Apache Spark batch pipeline, 3 data sizes, shuffle evidence, boundary + skew tests |
| 2 | `run_task2.py` | Batch vs event-time streaming (watermark, de-dup), counterexample, restart, 2-second requirement, Spark Structured Streaming |
| 3 | `run_task3.py` | Role views + hash-chained audit, linkage attack, k-anonymity lattice, AES-256-GCM, HMAC/SHA-256 tamper detection |
| 4 | `run_task4.py` | Cleaning stage with quarantine, decision trace, duplicate prediction, schema drift (km/h -> m/s) |
| 5 | `run_task5.py` | 5M events in CSV, Parquet and SQLite: size, bytes read, time, tuning, write load, changed queries |
| 6 | `run_task6.py` | Fraud-link detector: naive O(n^2) vs keyed sliding window, hand-checked test, growth and skew |

## Run
```
python -m venv .venv && .venv\Scripts\activate      # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt                     # Java 17+ required for Spark
python run_task1.py                                 # ... or: bash run_all.sh
```
Take your own VS Code screenshots by running each script in the VS Code terminal. `make_screenshots.py` only renders the saved logs.

## Notes
* Executed on one machine (1 core, 4 GB RAM, Spark local mode); not on a cloud cluster. To run on a cloud VM/Dataproc/HDInsight, copy the folder and run the same commands.
* Kafka was not used; Spark Structured Streaming reads micro-batches from a file source.
* `tests/part1_events.json` holds placeholder events for Task 6.3 - replace with the eight events of Part I Task 6.
* All data is synthetic and seeded.

## Upload to GitHub
```
git init
git add .
git commit -m "CO4 Part II big data engineering"
git branch -M main
git remote add origin https://github.com/<your-user>/CO4_BigData_Assignment.git
git push -u origin main
```
