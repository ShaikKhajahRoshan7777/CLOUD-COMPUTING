"""Builds docs/CSA15_Assignment4_PartI_Submission.docx:
   pages 1-4 = the ORIGINAL uploaded document, untouched; page 5 onward = the documented answers."""
import os, sys, copy
import docx
from docx.oxml.ns import qn
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, f"{ROOT}/scripts"); sys.path.insert(0, f"{ROOT}/tools")
from docx_helpers import *
from task1_spec_data import STAGES as S1, DEFENCE, FIELDS

SRC = os.environ.get("SRC", "/mnt/user-data/uploads/CO4-A_ASSIGN_QUESTIONS.docx")
doc = docx.Document(SRC)
body = doc.element.body
kids = list(body)
for el in kids[69:]:                      # elements 0-68 are pages 1-4 of the original; the question paper starts at 69
    if el.tag != qn("w:sectPr"): body.remove(el)
B = Builder(doc)
SS = f"{ROOT}/screenshots"; FG = f"{ROOT}/figures"
fx = lambda s: s.replace(" x 10^6", " × 10⁶").replace("10^6", "10⁶")

# ============================================================ ANSWER SUBMISSION (page 5)
B.h1("ANSWER SUBMISSION — BIG DATA SOLUTION DESIGN THROUGH SPECIFICATION")
B.p("**CSA15 – Cloud Computing and Big Data Analytics  |  Assignment 4 – Part I  |  CO4  |  50 Marks**", "c", color=NAVY)
B.p("This section contains the documented answers to Tasks 1–6. Every answer follows the progression required by the assignment: "
    "**Interpret the Scenario → Characterise the Data → Identify the Dominant Challenge → Design the Pipeline → Specify → Trace → Challenge → Refine.** "
    "All designs are written in the Pipeline Specification Template shown on page 4 (INPUT, PROCESS, OUTPUT, STORAGE, LATENCY, SECURITY). "
    "No framework, product, code or configuration is used as a design decision. Where a number is not given in the question it is marked as an **assumption** or an **estimate**.", "j")
B.h2("How the evidence is organised")
B.grid(["Task", "Topic", "Marks", "Evidence provided in this document"],
       [["1", "Diagnose and repair a pipeline (hospital analytics)", "6", "8 deficiencies, 6-stage repaired specification with a data-protection rule per stage, 79-word defence"],
        ["2", "Requirement to specification (smart-city traffic)", "8", "Problem model, stream + batch hypothesis, 7-stage specification, 8-event trace, modified-case prediction"],
        ["3", "Capacity and sizing (agriculture and weather)", "9", "Quantities, formulas, 12-step sizing specification, 220.05 TB, 4 nodes, doubled-imagery case, dependency"],
        ["4", "Design forensics (security and privacy)", "7", "Quasi-identifier defect, 7-record failing case with linkage trace, minimal repair to step 3, regression"],
        ["5", "Processing models (MapReduce, in-memory, stream)", "7", "Key-value design with (sum, count) combiner, iteration cost, in-memory recovery, watermark trade-off"],
        ["6", "Independent design (welfare fraud and sharing)", "13", "Abstraction, strategy with rejected options, state formulation, 8-stage specification, E1–E8 trace, attack on own design"]],
       [600, 3000, 700, 4726], center=(0, 2))
B.callout("The Python scripts in the accompanying GitHub folder are used only to check arithmetic and to repeat the manual desk-checks; the output screenshots (taken from VS Code) are evidence of that checking. "
          "They are not a substitute for the specifications, in line with Important Instruction 3 of the assignment.", title="Role of the Python output screenshots")

# ============================================================ TASK 1
B.h1("TASK 1 — DESIGN REVIEW: Diagnose and Repair a Poor Pipeline Design (6 Marks)")
B.h2("Task 1.1 – Diagnose the Design  |  2 Marks")
B.p("The junior engineer's five lines name activities but state no decision that can be tested. Eight deficiencies are identified, each with the reason another engineer could not build the system reliably from the text.", "j")
B.grid(["#", "Original line", "Deficiency", "Why it cannot be built reliably"],
 [["1", "Collect data from hospitals", "Sources, formats and arrival pattern are not stated. EHR extracts (structured, continuous), lab reports (files, daily) and medical images (very large binaries) behave differently.",
   "The engineer cannot choose the transfer mode, schedule or capacity. Images (about 3 TB/day) would swamp records (about 12 GB/day) if treated alike."],
  ["2", "Collect data from hospitals", "No authentication or integrity check at collection: nothing proves which hospital sent a file or whether it is complete.",
   "A truncated, duplicated or spoofed file would be accepted; the engineer has no rule for rejecting it."],
  ["3", "Store data everywhere", "No location, zone, replication, retention period or legal residency rule.",
   "'Everywhere' gives no rule for where a record may live; copies multiply and cannot be deleted at the end of retention."],
  ["4", "Clean the data", "'Clean' is undefined: no checks are named and the fate of a bad record is not stated.",
   "Two engineers would implement different checks; bad records may be silently dropped or may distort the disease counts."],
  ["5", "(whole pipeline)", "Sensitive personal health data is not addressed: no de-identification, consent, encryption or separation of identifiers.",
   "The engineer cannot know which fields must be removed before analysis; the design may breach the law on personal data."],
  ["6", "Analyse the data", "'Analyse' has no definition (which trend, unit, frequency, threshold) and no volume, latency or retention expectation.",
   "Compute cannot be sized and nobody can judge whether the output is correct or on time."],
  ["7", "Share results with everyone", "'Everyone' has no access model: no tiers, approvals or protection against re-identification from small counts.",
   "Authorisation cannot be implemented; public tables with very small counts could identify patients."],
  ["8", "(whole pipeline)", "No failure handling, replay or audit trail.",
   "The engineer cannot decide what happens when a hospital feed stops half-way, and cannot show who accessed which data."]],
 [400, 1500, 3500, 3626], center=(0,))
B.h2("Task 1.2 – Repair the Design  |  3 Marks")
B.p("**Assumptions (not given in the question):** 300 hospitals; about 20,000 EHR and lab records per hospital per day = 6 × 10⁶ records/day at about 2 KB = about 12 GB/day; about 200 imaging studies per hospital per day at 50 MB = 3 TB/day; raw data retained 7 years, de-identified data 10 years; minimum group size k = 10 for any published or released cell.", "j")
B.figure(f"{FG}/fig_task1_pipeline.png", "Repaired HospitalAnalytics pipeline with identified and de-identified zones")
B.callout("PIPELINE HospitalAnalytics\n   Stages 1–6 below, each stating INPUT, PROCESS, OUTPUT, STORAGE, LATENCY, SECURITY\nEND PIPELINE", title="Repaired specification", fill=LIGHT, edge=NAVY)
cols = [NAVY, NAVY, ORANGE, TEAL, TEAL, GOLD]
for (no, name, f), c in zip(S1, cols):
    B.spec(no, name, {k: fx(v) for k, v in f.items()}, FIELDS, c)
B.h2("Data-protection rule applied at each stage")
B.grid(["Stage", "Rule that protects personal data", "What it prevents"],
 [["1 Intake", "Mutual TLS; write-only hospital credentials; AES-256 at rest", "Spoofed senders; one hospital reading another's files"],
  ["2 Validate", "Quarantine holds identifiers, so it has the raw zone's access class; logs hold reason codes only", "Identifiers leaking through error handling and logs"],
  ["3 De-identify", "Keyed pseudonym, age band, 3-digit PIN, month-level dates, groups below 10 suppressed", "Re-identification by linking quasi-identifiers (see Task 4)"],
  ["4 Analyse", "Role Epidemiologist on the Curated Zone only; small cells screened before writing", "Analysts reaching raw data; small counts exposing patients"],
  ["5 Share", "No identifiers in any tier; approval ticket; MFA; expiring links", "Over-sharing to 'everyone'"],
  ["6 Audit", "Append-only, separate audit store; nobody can erase entries", "Undetectable misuse; loss of accountability"]],
 [1300, 4500, 3226])
B.h2("Task 1.3 – Design Defence  |  1 Mark")
B.callout(DEFENCE + f"\n__(Word count: {len(DEFENCE.split())})__", title="Defence (not more than 100 words)", fill="E8F5EE", edge=GREEN)
B.figure(f"{SS}/task1_spec_check_vscode_output.png", "VS Code output of task1_spec_check.py — all six stages complete, defence within the word limit", 6.2)

# ============================================================ TASK 2
B.h1("TASK 2 — FROM BUSINESS REQUIREMENT TO PIPELINE SPECIFICATION: Smart City Traffic Analytics (8 Marks)")
B.h2("Task 2.1 – Model the Requirement  |  2 Marks")
B.kv([("Input", "50,000 road sensors, one event per second each: Sensor ID | Road Segment | Speed (km/h) | Event Time, sent over the network. **Rate = 50,000 events/s. Daily volume = 50,000 × 86,400 = 4.32 × 10⁹ events/day.** At an assumed 40 bytes per event this is about 2 MB/s and 172.8 GB/day raw (about 63 TB/year)."),
      ("Output and consumers", "(1) Average speed per road segment per one-minute interval, shown to the traffic control room. (2) A historical archive of valid events and window results for city planners."),
      ("Objective and latency", "Show each minute's average within seconds (target ≤ 5 s from the data arriving; provisional values refreshed every 5 s). Archive complete within hours; nightly correction of the previous day."),
      ("Constraints", "**Data quality:** events may be duplicated, missing speed, invalid, or delayed. **Retention (assumed):** live results 24 h, archive 5 years, raw log 7 days for replay. **Availability:** control room 24 × 7; loss of one ingest node must not lose events. **Lateness:** late events up to 60 s must still be reflected."),
      ("Decisions to be made", "For every event: is it valid? is it a duplicate? which window does it belong to (event time)? is it late and, if so, accepted or diverted? When is a window final and its result emitted?"),
      ("Information needed to decide", "**Valid:** sensor registered; speed present and 0–200; event time not in the future; segment equals the sensor's registered segment. **Duplicate:** set of (Sensor ID, Event Time) keys already seen. **Late:** the event's window end compared with the watermark (maximum event time seen minus 5 s).")])
B.h2("Task 2.2 – Formulate a Design Hypothesis  |  1 Mark")
B.callout("A combined approach: a stream pipeline computes event-time, one-minute, per-segment averages with a watermark and bounded allowed lateness for the control room, while the same validated events are archived continuously and re-processed in a nightly batch that corrects history.", title="Hypothesis (one sentence)", fill=LIGHT, edge=NAVY)
B.p("**Why it suits the data.** The data is continuous, unbounded and arrives at 50,000 events/s, and the control room needs results within seconds, so batch alone is too slow. Event time and arrival time differ (duplicates and network delays), so windows must follow event time. Streaming can only wait a bounded time for late events; the archive must still be exact for planning, so a batch recomputation over the complete archive is used to correct what the live view missed.", "j")
B.h2("Task 2.3 – Design the Pipeline  |  3 Marks")
O = FIELDS
T2 = [
 ("1", "INGEST AND BUFFER", {"INPUT": "50,000 events/s (about 2 MB/s) from registered sensors, JSON over a secure channel.",
   "PROCESS": "Authenticate the sensor; APPEND every event unchanged, with its arrival time, to a durable log split into 32 partitions by hash(Sensor ID). Acknowledge only after the write is held on 3 replicas.",
   "OUTPUT": "Raw event log read by Stage 2 and by the archive writer (Stage 6).", "STORAGE": "Replicated log, retained 7 days to allow replay.",
   "LATENCY": "Event in the log within 1 s of arrival.", "SECURITY": "Device certificates and TLS; only registered sensors accepted; log encrypted at rest."}),
 ("2", "VALIDATE", {"INPUT": "Events from the log.",
   "PROCESS": "An event is VALID only if: sensor registered AND speed present AND 0 ≤ speed ≤ 200 AND event time not more than 5 s in the future AND segment equals the sensor's registered segment. Otherwise send to dead-letter with a reason code (NULL_SPEED, RANGE, UNKNOWN_SENSOR, FUTURE_TIME). Invalid events never enter an average.",
   "OUTPUT": "Valid events to Stage 3; rejects to a data-quality dashboard.", "STORAGE": "Dead-letter store, 30 days.", "LATENCY": "At most 0.5 s per event.",
   "SECURITY": "Dead-letter readable by the data-quality team only."}),
 ("3", "DEDUPLICATE (state 1)", {"INPUT": "Valid events.",
   "PROCESS": "KEY = (Sensor ID, Event Time). If the key is in the seen-set, MERGE: discard the repeat and count it in a duplicate metric. Otherwise add the key. A key is removed when the watermark passes its event time + 120 s (window 60 s + lateness 60 s). Estimated state: 50,000 sensors × 120 keys = 6 × 10⁶ keys.",
   "OUTPUT": "Unique valid events to Stage 4.", "STORAGE": "Seen-set held in memory, partitioned like the log, checkpointed every 10 s.", "LATENCY": "At most 0.5 s.",
   "SECURITY": "State store not reachable from outside the pipeline."}),
 ("4", "WINDOW AND AGGREGATE (state 2)", {"INPUT": "Unique valid events.",
   "PROCESS": "WINDOW by EVENT TIME (never arrival time): tumbling one-minute windows [hh:mm:00, hh:mm+1:00) per road segment, holding (sum of speed, count). WATERMARK W = maximum event time seen − 5 s. When W ≥ window end, emit FINAL average = sum / count. LATE event for a window already final: if W − window end ≤ 60 s (allowed lateness), add it and emit a CORRECTION; otherwise divert it to the late archive for the nightly batch. Open windows emit a PROVISIONAL average every 5 s. Estimated state: about 5,000 segments × 2 open windows = 10,000 accumulators.",
   "OUTPUT": "(segment, window start, average, count, status) with status PROVISIONAL, FINAL or CORRECTION.", "STORAGE": "Accumulators in memory with a 10 s checkpoint; discarded at window end + 60 s.",
   "LATENCY": "Provisional ≤ 5 s; final within about 10 s of window end.", "SECURITY": "Output holds no sensor IDs, only segment aggregates."}),
 ("5", "SERVE", {"INPUT": "Window results from Stage 4.", "PROCESS": "UPSERT by (segment, window start) so a CORRECTION replaces the earlier value; keep the latest 24 h.",
   "OUTPUT": "Live display for the control room.", "STORAGE": "Fast key-value serving store, replicated on 2 sites, 24 h hot retention.", "LATENCY": "Visible within 2 s of emission.",
   "SECURITY": "Operators have read-only access; TLS on all connections."}),
 ("6", "ARCHIVE", {"INPUT": "Valid unique events, diverted late events and window results.",
   "PROCESS": "Write to columnar files partitioned by date and segment. NIGHTLY BATCH recomputes the previous day's one-minute averages from all valid events (including late ones), replaces the archived results and logs any difference from the live values.",
   "OUTPUT": "Planning datasets and corrected history.", "STORAGE": "Compressed archive, retained 5 years.", "LATENCY": "Events appended within 15 min; nightly job finished within 2 h.",
   "SECURITY": "Planners read only; only the pipeline writes; raw partitions immutable."}),
 ("7", "FAILURE AND REPLAY", {"INPUT": "Checkpoints, log offsets and health signals.",
   "PROCESS": "Checkpoint state and log offsets every 10 s. On failure restart from the last checkpoint and re-read the log from the stored offset; de-duplication and UPSERT make a replay produce identical results. If a segment has no events for 3 consecutive minutes, raise an alert. If an ingest node fails, its partitions move to the remaining nodes.",
   "OUTPUT": "Recovered state; alerts to operations.", "STORAGE": "Checkpoints kept 24 h.", "LATENCY": "Recovery within 60 s.", "SECURITY": "Operator actions logged; checkpoints encrypted."}),
]
B.callout("PIPELINE TrafficAnalytics  —  7 stages: Ingestion and buffering (1) · Validation (2) · De-duplication and state (3) · Event-time windows, watermark, late events and state (4) · Output and serving (5) · Archive (6) · Failure and replay (7)", fill=LIGHT, edge=NAVY)
for (no, nm, f), c in zip(T2, [NAVY, NAVY, TEAL, TEAL, ORANGE, GOLD, RED]): B.spec(no, nm, f, O, c)
B.h2("Task 2.4 – Desk-Check  |  1 Mark")
B.p("One-minute event-time windows; watermark = maximum valid event time seen − 5 s; allowed lateness 60 s; valid speed 0–200.", keep=True)
B.grid(["No.", "Sensor", "Seg.", "Speed", "Event time", "Arrival", "Decision", "State after the event"],
 [["1", "S1", "R7", "42", "08:00:05", "08:00:06", "ACCEPTED", "R7@08:00: sum 42, n 1"],
  ["2", "S2", "R7", "38", "08:00:20", "08:00:21", "ACCEPTED", "R7@08:00: sum 80, n 2"],
  ["3", "S1", "R7", "42", "08:00:05", "08:00:07", "MERGED (key S1, 08:00:05 already seen)", "unchanged: sum 80, n 2"],
  ["4", "S3", "R9", "missing", "08:00:30", "08:00:31", "REJECTED, NULL_SPEED", "unchanged"],
  ["5", "S2", "R7", "−5", "08:00:50", "08:00:51", "REJECTED, RANGE (outside 0–200)", "unchanged"],
  ["6", "S4", "R9", "55", "08:01:10", "08:01:12", "ACCEPTED. W becomes 08:01:05 ≥ 08:01:00, so window R7@08:00 closes: FINAL 40.0 (n 2)", "R7@08:00 sum 80 n 2 (final); R9@08:01 sum 55 n 1"],
  ["7", "S1", "R7", "40", "08:00:45", "08:01:40", "LATE-ACCEPTED: window final, lag W − end = 5 s ≤ 60 s, CORRECTION emitted", "R7@08:00 sum 120, n 3, avg 40.0"],
  ["8", "S5", "R9", "60", "08:01:20", "08:01:21", "ACCEPTED", "R9@08:01 sum 115, n 2 (provisional 57.5)"]],
 [450, 650, 550, 750, 1000, 1000, 2600, 2026], center=(0, 1, 2, 3))
B.grid(["Output", "Value", "Meaning"],
 [["R7, 08:00–08:01", "FINAL 40.0 (n = 2), then CORRECTION 40.0 (n = 3)", "E1 and E2 only at close; E7 added late. The average is unchanged only because 40 equals the earlier mean of 42 and 38."],
  ["R9, 08:00–08:01", "no row", "E4 was rejected, so the window has no valid event."],
  ["R9, 08:01–08:02", "PROVISIONAL 57.5 (n = 2)", "(55 + 60) / 2; final when W ≥ 08:02:00."]],
 [1800, 3000, 4226])
B.figure(f"{FG}/fig_task2_windows.png", "Events E1–E8 placed in one-minute event-time windows with their decisions")
B.figure(f"{SS}/task2_traffic_trace_vscode_output.png", "VS Code output of task2_traffic_trace.py (decision trace and modified-case check)", 6.2)
B.h2("Task 2.5 – Challenge Your Design  |  1 Mark")
B.p("**Change made:** the speed of event 7 is changed from 40 to **52** (all other values unchanged).", keep=True)
B.kv([("(1) Prediction", "The output **will change**: window R7 08:00 will be corrected from 40.0 to (42 + 38 + 52) / 3 = **44.0**."),
      ("(2) Decision expected to be affected", "Only the decision for E7 (late-accept and re-emit a correction). E1–E6 and E8 are untouched because the change comes after the window was final."),
      ("(3) Relevant trace", "E7: key (S1, 08:00:45) not in seen-set, so it is not a duplicate. Window R7 08:00 already final, lag W − end = 5 s ≤ 60 s, so LATE-ACCEPTED. Sum 80 + 52 = 132, n = 3, average = 44.0, CORRECTION emitted."),
      ("Result", "**Prediction correct** (confirmed by the script: sum = 132, n = 3, average = 44.0).")])
B.p("**Parameter check.** If the allowed lateness were 0 s, E7 (lag 5 s) would be diverted to the late archive: the live display would stay at 40.0 (n = 2) and only the nightly batch would include E7. A longer allowance gives more complete live values but keeps state longer; a shorter one finalises sooner but pushes more data to the nightly correction.", "j")

# ============================================================ TASK 3
B.h1("TASK 3 — FROM CAPACITY REQUIREMENT TO SIZING SPECIFICATION: Agriculture and Weather Data Platform (9 Marks)")
B.h2("Task 3.1 – Define the Quantities  |  1 Mark")
B.p("Decimal units are used: 1 TB = 1,000 GB and 1 GB = 1,000 MB.", keep=True)
B.grid(["Symbol", "Quantity", "Unit", "What it represents"],
 [["Ns, r, b", "Stations, readings per minute per station, bytes per reading", "5,000; 1; 400 B", "Input rate of the weather and soil stations"],
  ["c", "Compression ratio for weather data", "3 : 1", "Weather readings shrink to one third when stored; imagery does not compress"],
  ["Vw", "Daily raw weather volume", "GB/day", "Ns × r × 1,440 × b before compression"],
  ["Vi", "Daily raw imagery volume", "GB/day", "200 GB/day, not compressible"],
  ["Sd", "Daily stored volume (one copy)", "GB/day", "Vw / c + Vi: what one copy of a day's data occupies"],
  ["R, T", "Replication factor, retention", "3; 365 days", "Copies kept of each block; days of history retained"],
  ["Syr", "One-year replicated storage", "TB", "Sd × T × R: total disk consumed after one year"],
  ["Cnode", "Usable capacity per node", "TB", "Disks × disk size × usable fraction = 12 × 8 × 0.70"],
  ["Bnode", "Scan throughput per node", "MB/s", "12 disks × 150 MB/s, disks read in parallel"],
  ["W, Qscan", "Scan window; data to scan", "s; GB", "2 h = 7,200 s; previous day's stored data = Sd (one replica)"],
  ["ns, np, n", "Nodes for storage, for the scan, final", "nodes", "Whole nodes needed by each constraint and the cluster size chosen"]],
 [900, 3000, 1300, 3826], center=(0,))
B.h2("Task 3.2 – Develop the Formulas  |  2 Marks")
B.grid(["#", "Formula", "Meaning of the terms"],
 [["F1", "Vw = Ns × r × 1,440 × b", "1,440 minutes in a day; result in bytes, converted to GB"],
  ["F2", "Sd = Vw / c + Vi", "Compression divides only the weather term; imagery is added unchanged"],
  ["F3", "Syr = Sd × T × R", "Retention multiplies days kept; **replication multiplies because every block is physically stored R times**"],
  ["F4", "Cnode = D × Cdisk × u", "**Usable fraction u = 0.70 appears here** because only 70% of raw disk can hold data (the rest is file-system overhead, temporary space and headroom)"],
  ["F5", "ns = ceil( Syr / Cnode )", "Nodes needed to hold one year of replicated data; ceil because nodes are whole"],
  ["F6", "np = ceil( Sd / ( D × Bdisk × W ) )", "Data to scan divided by what one node can read in the window. **Replication is absent**: a scan reads one replica of each block"],
  ["F7", "n = max( ns, np )", "Both limits must hold at the same time, so the larger one governs"]],
 [600, 3300, 5126], center=(0,))
B.h2("Task 3.3 – Translate into a Sizing Specification  |  4 Marks")
B.kv([("Assumptions and inputs", "5,000 stations × 1 reading/min × 400 B, compressible 3 : 1. Imagery 200 GB/day, not compressible. Replication 3. Retention 365 days. Node = 12 disks × 8 TB, 70% usable, disks read in parallel at 150 MB/s each. Scan window 2 h for the previous day's data. Decimal units. __(The scan reads one replica of the previous day's stored data: assumption.)__")], (2300, 6726), head="SIZING SPECIFICATION  AgriWeatherPlatform", head_fill=NAVY)
B.grid(["Step", "Computation", "Result"],
 [["1", "Weather readings per day = 5,000 × 1,440 × 1", "7,200,000"],
  ["2", "Weather raw volume = 7,200,000 × 400 B", "2.88 GB/day"],
  ["3", "Imagery raw volume", "200.00 GB/day"],
  ["4", "Total raw volume = 2.88 + 200", "202.88 GB/day"],
  ["5", "Weather stored = 2.88 / 3", "0.96 GB/day"],
  ["6", "Total stored per day = 0.96 + 200", "200.96 GB/day"],
  ["7", "One-year replicated storage = 200.96 × 365 × 3", "220,051.2 GB = 220.05 TB"],
  ["8", "Usable capacity per node = 12 × 8 × 0.70", "67.2 TB"],
  ["9", "Nodes for storage = ceil( 220.05 / 67.2 ) = ceil( 3.27 )", "4 nodes"],
  ["10", "Scan rate per node = 12 × 150 MB/s; in 2 h = 1,800 × 7,200 MB", "1,800 MB/s; 12.96 TB"],
  ["11", "Nodes for scan = ceil( 200.96 GB / 12,960 GB ) = ceil( 0.016 )", "1 node"],
  ["12", "Final nodes = max( 4, 1 )", "**4 nodes — storage governs**"]],
 [700, 5600, 2726], center=(0,))
B.callout("Imagery rises from 200 to 400 GB/day. Stored per day = 0.96 + 400 = 400.96 GB. Replicated year = 400.96 × 365 × 3 = 439,051 GB = 439.05 TB. Storage nodes = ceil( 439.05 / 67.2 ) = ceil( 6.53 ) = **7**. Scan nodes = ceil( 400.96 / 12,960 ) = 1. **Final = 7 nodes (from 4): storage still governs, and doubling imagery raises the cluster by 75%.**", title="If imagery doubles", fill=CALL)
B.h2("Task 3.4 – Desk-Check  |  1 Mark")
B.figure(f"{FG}/fig_task3_capacity.png", "Daily stored volume by source and the two node requirements")
B.p("All intermediate results are the ones shown in the table above and are reproduced by the script (Figure 6). **Imagery dominates storage:** 200 of 200.96 GB/day, which is **99.5%**. This matters because capacity planning should target imagery, not the weather feed: imagery lifecycle (move older scenes to cold storage), a lower-overhead protection scheme for imagery, or keeping derived products instead of every raw scene would shrink the cluster far more than any tuning of weather data. As an estimate, protecting imagery with about 1.5 × overhead instead of 3 × would need 200.96 × 365 × 1.5 = 110.03 TB, i.e. 2 nodes, at the price of slower recovery and a different failure model.", "j")
B.figure(f"{SS}/task3_sizing_vscode_output.png", "VS Code output of task3_sizing.py (all twelve steps and the doubled-imagery case)", 6.2)
B.h2("Task 3.5 – Explain the Dependency  |  1 Mark")
B.p("The cluster must satisfy two independent limits at once: it must be able to **hold** one year of replicated data (step 9) and it must be able to **read** the previous day's data inside the two-hour window (step 11). Each formula gives only a lower bound; a cluster with enough disks but too little read throughput would miss the nightly window, and one with enough throughput but too few disks could not hold the data. Neither bound alone is the answer, so the specification computes volumes (steps 1–7), then storage nodes (steps 8–9), then scan nodes (steps 10–11), and only then takes the maximum (step 12). Here storage requires 4 nodes and the scan only 1, so the 4-node cluster passes the scan test easily (4 × 12.96 TB per window against about 0.2 TB to read). The order matters because with other inputs (for example a 30-day scan) the scan could be the larger number.", "j")

# ============================================================ TASK 4
B.h1("TASK 4 — DESIGN FORENSICS: Find, Explain and Repair a Security Defect (7 Marks)")
B.h2("Task 4.1 – Locate the Defect  |  2 Marks")
B.p("**The incomplete decision is step 3.** It treats only Name and ID_Number as identifying and releases PIN_Code, Date_of_Birth and Gender exactly as stored. These three are **quasi-identifiers**: none identifies a person alone, but their combination is almost unique and also appears in public lists (voter or membership rolls) that carry names.", "j")
B.p("**Why removing direct identifiers is not enough.** A record is identified when its combination of attributes matches exactly one person in some outside dataset. A single PIN-code area may hold about 20,000 people, while PIN × date of birth × gender offers about 29,000 birth dates (80 years) × 2 = 58,000 combinations, so most people occupy a combination of their own. Published studies of census data have found that the large majority of a population is unique on postal code, birth date and sex. Step 3 never checks how many released rows share a combination, so it removes the columns but not the risk.", "j")
B.p("__Other weaknesses (perimeter-only protection, one shared account, audit logs on the same cluster) exist but are outside this task.__", italic=False)
B.h2("Task 4.2 – Construct a Failing Case  |  2 Marks")
B.p("**Released table** (output of the original step 3, 7 records) and a **public voter list** (5 people) designed for this task:", keep=True)
B.grid(["Rec.", "PIN_Code", "Date_of_Birth", "Gender", "Scheme", "Amount (Rs)"],
 [["1", "600117", "1985-03-14", "F", "Widow Pension", "1,200"], ["2", "600042", "1988-11-02", "F", "Housing", "8,000"],
  ["3", "600117", "1991-07-21", "M", "Scholarship", "5,000"], ["4", "600089", "1993-01-30", "M", "Housing", "8,000"],
  ["5", "600042", "1996-05-09", "M", "Farmer Aid", "3,000"], ["6", "600089", "1984-12-25", "F", "Scholarship", "5,000"],
  ["7", "600117", "1990-08-15", "M", "Farmer Aid", "3,500"]], [600, 1400, 1800, 1100, 2326, 1800], center=(0, 1, 2, 3, 5))
B.grid(["Name (public list)", "PIN_Code", "Date_of_Birth", "Gender"],
 [["Meena S", "600117", "1985-03-14", "F"], ["Priya R", "600042", "1988-11-02", "F"], ["Anil K", "600089", "1993-01-30", "M"],
  ["Karthik V", "600117", "1991-07-21", "M"], ["Ravi T", "600055", "1979-02-02", "M"]], [2600, 2000, 2400, 2026], center=(1, 2, 3))
B.p("**Linking steps.** (1) Take each name in the public list. (2) Join to the release on PIN_Code = PIN_Code AND Date_of_Birth = Date_of_Birth AND Gender = Gender. (3) Count matching rows. (4) If exactly one row matches, the person is identified and the sensitive attributes are learned.", keep=True)
B.grid(["Person", "Matches in release", "Outcome"],
 [["Meena S", "1 (record 1)", "**RE-IDENTIFIED: first identification occurs here, at step (3).** Receives Widow Pension, Rs 1,200"],
  ["Priya R", "1 (record 2)", "Re-identified: Housing, Rs 8,000"], ["Anil K", "1 (record 4)", "Re-identified: Housing, Rs 8,000"],
  ["Karthik V", "1 (record 3)", "Re-identified: Scholarship, Rs 5,000"], ["Ravi T", "0", "No match (not a beneficiary)"]], [1700, 2100, 5226])
B.figure(f"{SS}/task4_linkage_attack_vscode_output.png", "VS Code output of task4_linkage_attack.py (linkage attack, repair and regression check)", 6.2)
B.h2("Task 4.3 – Repair the Design  |  2 Marks")
B.callout("3′. DE-IDENTIFICATION (replaces step 3 only; steps 1, 2 and 4 unchanged)\n"
          "   a. DROP Name and ID_Number.\n   b. GENERALISE PIN_Code to its first 3 digits.\n   c. GENERALISE Date_of_Birth to its decade of birth.\n   d. KEEP Gender, Scheme, Amount.\n"
          "   e. GROUP rows by (PIN3, decade, Gender). If any group has fewer than k = 3 rows, SUPPRESS those rows or generalise further.\n"
          "   f. RELEASE only when every group has at least k rows and at least 2 distinct Scheme values.", title="Corrected step 3", fill="E8F5EE", edge=GREEN)
B.p("**Verification on the failing case.** After generalisation the 7 records form two groups: (600, 1980s, F) = records 1, 2, 6 (3 rows, 3 different schemes) and (600, 1990s, M) = records 3, 4, 5, 7 (4 rows, 3 different schemes). Re-running the join on the generalised keys gives Meena S, Priya R: 3 candidates each; Anil K, Karthik V: 4 candidates each; Ravi T: none. **No person now matches a single row; the best an attacker can do is probability 1/3.** The different schemes inside each group also stop group membership from revealing the scheme. __k = 3 suits this 7-record demonstration; a real release would use a larger k (for example 10), as in Task 1.__", "j")
B.h2("Task 4.4 – Regression Check  |  1 Mark")
B.grid(["Check", "Original design", "Repaired design", "Verdict"],
 [["Ravi T (not a beneficiary) joined to the release", "0 matches", "0 matches", "Behaviour preserved: still no information about him"],
  ["Query: average Amount per Scheme", "Farmer Aid 3,250; Housing 8,000; Scholarship 5,000; Widow Pension 1,200", "Identical values", "Analysis unaffected: Scheme and Amount are untouched"]],
 [2500, 2300, 2000, 2226])
B.p("Gender, Scheme and Amount are kept, and location and age remain usable at district-prefix and decade level, so the release stays useful for analysis while the identification route is closed.", "j")

# ============================================================ TASK 5
B.h1("TASK 5 — SAME DATA, DIFFERENT PROCESSING MODELS: MapReduce, In-Memory and Stream Processing (7 Marks)")
B.h2("Task 5.1 – Design a MapReduce Computation  |  3 Marks")
B.kv([("Map input", "Archive files split into 128 MB blocks; each map task reads one split of records (Sensor ID, Segment, Speed, Event Time). Records with missing or negative speed are skipped."),
      ("Map output (key-value pairs)", "**key = (Segment, Hour)** where Hour is Event Time truncated to the hour; **value = (Speed, 1)**."),
      ("Combiner", "On each mapper, for every key, replace its pairs by **(sum of speeds, sum of counts)**. The count must be carried: an average of partial averages is wrong. On the sample, the correct average for R9 is 50.00 but the average of the two partial averages is 51.88."),
      ("Partitioning and shuffle", "reducer = hash(Segment, Hour) mod R, so all pairs of one key reach one reducer. Mapper output is sorted by key and spilled to the mapper's local disk; each reducer fetches its partition over the network and merges it."),
      ("Reduce logic and output", "For each key: S = sum of the received sums, N = sum of the received counts; output **(Segment, Hour, S / N, N)**."),
      ("Where intermediate data is written", "Map output and shuffle spills: **local disks of the mapper nodes** (not replicated). Final output: one file per reducer in the **replicated distributed file store**.")],
     (2300, 6726), head="MAPREDUCE  HourlyAverageSpeed", head_fill=NAVY)
B.p("**Shuffle reduction (estimate, not measured).** Without a combiner every event is shuffled: 4.32 × 10⁹ pairs. If each mapper reads one hour of data (1.8 × 10⁸ events) and there are about 5,000 segments, each mapper emits at most 5,000 pairs, so 24 mappers emit about 1.2 × 10⁵ pairs: roughly **36,000 times fewer**. The figure rests on those assumptions.", "j")
B.grid(["Step", "Mapper 1 (sample)", "Mapper 2 (sample)", "Reducer result"],
 [["Map emits", "R7: 42, 38, 40; R9: 55", "R7: 60; R9: 60, 50, 40, 45", "—"],
  ["After combiner", "(R7,08): (120, 3); (R9,08): (55, 1)", "(R7,08): (60, 1); (R9,08): (195, 4)", "—"],
  ["Reduce", "—", "—", "R7: 180 / 4 = 45.0;  R9: 250 / 5 = 50.0"]], [1500, 2700, 2700, 2126])
B.figure(f"{FG}/fig_task5_dataflow.png", "MapReduce stages and the disk reads needed for 20 iterations (estimate)")
B.figure(f"{SS}/task5_mapreduce_sim_vscode_output.png", "VS Code output of task5_mapreduce_sim.py (sample run and data-movement estimates)", 6.2)
B.h2("Task 5.2 – Change the Requirement: Iteration  |  2 Marks")
B.p("**The costly decision** is that every job **re-reads the full dataset from disk and writes its results to disk** (map spills, shuffle files and a replicated output) before the next job can start. Twenty iterations are twenty chained jobs, so the 172.8 GB/day dataset (assumed 40 B per event) is read 20 times, about **3,456 GB**, and every pass pays start-up, shuffle and replicated-write costs.", "j")
B.p("**In-memory model.** The dataset is loaded once into partitions held in the memory of the workers and cached. Each iteration is a set of transformations over those partitions; only small results (for example, cluster centres) are exchanged between workers. Disk is read once (172.8 GB), so about 3,283 GB (95%) of repeated reads is avoided (estimate).", "j")
B.p("**When a worker fails.** Its memory partitions are lost. The framework recomputes only those partitions from their **lineage** (the recorded chain of transformations back to the source files), or restores them from a checkpoint, while other workers continue. The cost is the recomputation of one partition's history, not a restart of all 20 iterations. The price of the model is memory: data that does not fit spills to disk.", "j")
B.h2("Task 5.3 – Change the Requirement: Real Time  |  2 Marks")
B.p("**Event time vs processing time.** Event time is when the measurement happened at the sensor; processing time is when the system handles it. They differ by network delay: event E7 in Task 2 happened at 08:00:45 but was processed at 08:01:40. Averages must follow event time, or delayed events land in the wrong minute.", "j")
B.p("**Windowing rule.** For alerts within 5 s, per segment, evaluate a 30-second sliding window in event time that advances every 1 s, and test the alert condition on its provisional content at each advance. An event can therefore alert about 1 s (slide) plus about 2 s (ingestion and processing) after it happens, inside the 5 s budget (estimate, not measured).", "j")
B.p("**Watermark and late events.** The watermark W = maximum event time seen − 2 s says \"events older than W are unlikely to arrive\"; it decides when a window is final, not when an alert fires. An event behind W is **late**. If it arrives within the **allowed lateness** (for example 30 s) it is added and may raise a correction; beyond that it is dropped from the live view and left to the batch archive.", "j")
B.p("**What allowed lateness trades off.** A longer allowance gives more complete and accurate results but holds window state longer (more memory), delays finality and can cause alerts that appear and are later withdrawn. A shorter allowance gives earlier final results and less state, but more valid events are discarded and counts are understated.", "j")

# ============================================================ TASK 6
B.h1("TASK 6 — DESIGN CHALLENGE: Fraud Detection and Controlled Data Sharing for a Welfare Platform (13 Marks)")
B.h2("Stage 1 – Interpret the Problem  |  2 Marks")
B.kv([("Input", "A stream of payment events from several departments. Each: Event | Beneficiary | Bank Account | District | Amount | Day. Events may be repeated; arrival is roughly in day order but can be delayed. Volume doubles within two years (assumed today: 2 × 10⁵ events/day, then 4 × 10⁵)."),
      ("Output", "(a) Fraud flags: event, rule and evidence, delivered with identifiers to analysts. (b) A de-identified research dataset for approved researchers."),
      ("Objective 1: detection", "As events arrive, flag **Rule A**: an account paid for three or more distinct beneficiaries within any 7-day window; **Rule B**: a payment more than three times the median of earlier payments in the same district (only when at least one earlier payment exists)."),
      ("Objective 2: sharing", "Provide researchers with data that carries no identifier and cannot single out an individual."),
      ("Constraints", "**Latency:** flags within about a minute of arrival (assumed). Sharing may be periodic (weekly). **Legal:** personal data protected by law; analysts need identifiers; researchers must never get identifiers or singling-out data. **Scale:** volume doubles in two years, so growth must come from adding partitions, not from redesign."),
      ("Decisions to be made", "Per event: valid? duplicate? update which state? does Rule A hold? does Rule B hold? which zone does it go to? Per release: which fields are removed or generalised? is every group large enough? who approved?"),
      ("Computational requirement", "Keep, per account, the beneficiaries paid in the last 7 days; keep, per district, enough of the earlier amounts to give their median."),
      ("Governance requirement (stated separately)", "G1 Identifiers (Beneficiary, Bank Account) exist only in a restricted identified zone used by fraud analysts. G2 A research release contains no identifier and no combination of values shared by fewer than k individuals. G3 Every access, release and approval is recorded. G4 Data is released only to approved researchers.")],
     (2300, 6726))
B.h2("Stage 2 – Propose the Strategy  |  2 Marks")
B.grid(["Option", "Verdict", "Reason from the problem's characteristics"],
 [["Batch only", "Rejected for detection", "Flags would appear only after the batch ends (hours), after the money is paid. Suitable only for the research release."],
  ["Stream only", "Rejected as the sole approach", "Rules A and B fit a stream, but a release needs whole-period grouping, the minimum-group-size check and reprocessing of corrections; releasing from a stream would publish groups before they are complete."],
  ["Processing at the source (each department)", "Rejected", "One account can be paid by several departments and a district median spans them; no single department sees enough data to apply Rule A or B."],
  ["**Stream for detection + batch for release and reconciliation**", "**Chosen**", "Detection state is small and keyed (per account, per district) so it scales by adding partitions; the release and the late-event reconciliation are bulk jobs by district and week."]],
 [2500, 1600, 4926])
B.p("**Why the principle suits the general problem, not just E1–E8.** State per account is bounded by the 7-day window (old beneficiaries are discarded) and state per district is a histogram of amounts, bounded by the number of distinct amounts, not by the number of payments. Work per event is small and independent per key, so when volume doubles the response is **twice the partitions and workers**, not a new design. The batch release is parallel by district and week, and larger volume makes groups bigger, which improves privacy.", "j")
B.h2("Stage 3 – Identify the Critical Information  |  2 Marks")
B.grid(["State", "Meaning", "Update on a new event", "Base condition", "Discard rule"],
 [["**A[account]**", "Map beneficiary → latest payment day, for the account's last 7 days (days d−6 to d)", "On event (b, a, d): delete entries with day < d − 6; set A[a][b] = d; n = number of entries; **flag A if n ≥ 3**", "Empty map; n = 0", "Entries older than d − 6 (plus 2 days of lateness tolerance); empty accounts removed"],
  ["**H[district]**", "Histogram of amounts of all earlier payments in the district (amount → count)", "Before inserting: if H is non-empty, m = median(H) and **flag B if amount > 3m**; then add the amount", "Empty histogram: Rule B not applied", "Kept for the programme's life; size bounded by distinct amounts (optional expiry is a policy decision)"],
  ["**Seen[event]**", "Event IDs already processed", "If the ID is present, DROP as duplicate", "Empty set", "IDs removed after 14 days"]],
 [1200, 2000, 2700, 1400, 1726])
B.p("**Keeping identifiers away from researchers.** The identified zone holds complete events. The research zone is filled only by a batch projection that drops Beneficiary, Bank Account and Event ID, generalises Day and Amount, and applies the minimum-group-size check. Any key or mapping used stays in the identified zone, researchers have no credentials or network path to it, and every release is approved and audited.", "j")
B.h2("Stage 4 – Design the Complete Specification  |  4 Marks")
O6 = FIELDS
T6 = [
 ("1", "INPUT AND INGESTION", {"INPUT": "Payment events (Event, Beneficiary, Account, District, Amount, Day) from each department; assumed 2 × 10⁵/day now, 4 × 10⁵/day in two years, about 100 B each.",
   "PROCESS": "Authenticate the department; APPEND each event unchanged to a durable partitioned log. Rule A reads the log partitioned by Account; Rule B reads a copy REPARTITIONED by District.",
   "OUTPUT": "Raw event log to Stage 2.", "STORAGE": "Log inside the identified zone, retained 30 days for replay.", "LATENCY": "Appended within 5 s.",
   "SECURITY": "Mutual TLS; write-only department credentials; encrypted at rest; log is part of the identified zone."}),
 ("2", "VALIDATE AND DEDUPLICATE", {"INPUT": "Events from the log.",
   "PROCESS": "REJECT to dead-letter (with reason) if any field is missing, Amount ≤ 0, Day is not a whole number or District is unknown. DEDUPLICATE on Event ID using Seen[event].",
   "OUTPUT": "Valid unique events to Stages 3 and 4; rejects to the data steward.", "STORAGE": "Seen-set in memory with checkpoint; dead-letter 90 days in the identified zone.", "LATENCY": "At most 2 s.",
   "SECURITY": "Dead-letter holds identifiers, so the same access class as the identified zone."}),
 ("3", "IDENTIFIED ZONE STORE", {"INPUT": "Valid unique events.",
   "PROCESS": "APPEND to the event store partitioned by Day and District; ENCRYPT the Beneficiary and Bank Account fields at field level.",
   "OUTPUT": "Source for investigations and for the batch release (Stage 6).", "STORAGE": "Identified zone, separate network segment, retained 7 years (assumed legal period).", "LATENCY": "Stored within 10 s.",
   "SECURITY": "Only role FraudAnalyst may read; no copy leaves the zone except through Stage 6."}),
 ("4", "RULE EVALUATION (STATE AND WINDOWS)", {"INPUT": "Valid unique events, in day order per key.",
   "PROCESS": "**Rule A** per account: apply State A (7-day window d−6 to d, flag when distinct beneficiaries ≥ 3). **Rule B** per district: apply State H (flag when amount > 3 × median of earlier payments; skip when none). An event may be flagged by both. A late event with an earlier Day (up to 2 days behind) is checked against the windows that contain it; older ones go to the weekly reconciliation batch.",
   "OUTPUT": "Flag records: Event ID, rule, evidence (for A the beneficiaries, for B the median and ratio).", "STORAGE": "State in memory, checkpoint every 30 s, inside the identified zone.", "LATENCY": "At most 10 s from validated event to flag.",
   "SECURITY": "State store unreachable from outside the zone; researchers have no access."}),
 ("5", "FLAGGING AND ALERT OUTPUT", {"INPUT": "Flag records.",
   "PROCESS": "WRITE each flag once per (Event ID, rule) to a case queue with its evidence and notify the assigned analyst. Keep the case open until the analyst records a decision.",
   "OUTPUT": "Alert with a link to the case, shown to analysts.", "STORAGE": "Case store in the identified zone, retained 7 years.", "LATENCY": "Analyst notified within 1 min of the event arriving.",
   "SECURITY": "Only assigned analysts open a case; notifications carry the case link, never full identifiers; every view is audited."}),
 ("6", "DE-IDENTIFIED ZONE AND RESEARCH RELEASE", {"INPUT": "Identified event store; weekly batch for the previous full week.",
   "PROCESS": "DROP Beneficiary, Bank Account and Event ID (replace by a random row number that is re-randomised for every release). GENERALISE Day to week number and Amount to a band of 1,000. KEEP District. GROUP by (District, Week, Amount band). If a group has fewer than k = 5 rows, SUPPRESS or merge it into a wider band. Release only if every group has at least 5 rows. Never publish an overlapping period with a different generalisation.",
   "OUTPUT": "Release file for approved researchers, with a release ID and k-check report.", "STORAGE": "Separate de-identified zone (own storage and network); release copies kept 3 years.", "LATENCY": "Built within 4 h of week end; delivered within 5 working days of approval.",
   "SECURITY": "The job reads the identified zone and writes only the de-identified zone; the steward reviews the k-check; no identifier field exists in the de-identified schema."}),
 ("7", "ACCESS CONTROL AND AUDIT", {"INPUT": "Every access, alert view, release and approval event.",
   "PROCESS": "ENFORCE roles: FraudAnalyst (identified zone), Researcher (de-identified zone after approval), Steward (approves releases), Engineer (no data access). Require MFA. APPEND an audit record (who, what, when, purpose) for each action. Review access monthly.",
   "OUTPUT": "Audit reports to the auditor and security officer.", "STORAGE": "Write-once audit store on a separate system, retained 7 years.", "LATENCY": "Audit record within 1 s of the action.",
   "SECURITY": "Separation of duties: an analyst cannot approve a release; nobody can edit or delete audit records."}),
 ("8", "FAILURE HANDLING, REPLAY AND GROWTH", {"INPUT": "Checkpoints, log offsets, job status, volume metrics.",
   "PROCESS": "CHECKPOINT state and offsets every 30 s. On failure restart from the last checkpoint and replay the log from the stored offset; alerts keyed by (Event ID, rule) make replay idempotent. If replay is needed beyond log retention, rebuild state by re-running stored events in Day order. GROWTH: partition by hash(Account) and hash(District); when volume doubles, double the partitions and workers; state per account stays bounded by the 7-day window.",
   "OUTPUT": "Recovered state; capacity alerts when load passes 70% of capacity.", "STORAGE": "Checkpoints kept 7 days in the identified zone.", "LATENCY": "Recovery within 5 min; scale-out within one maintenance window.",
   "SECURITY": "Restore only inside the identified zone; replay and scale-out actions are audited."}),
]
B.callout("PIPELINE WelfareFraudAndSharing  —  8 stages covering: input and ingestion (1) · validation and de-duplication (2) · identified zone (3) · state and window handling for Rules A and B (4) · flagging and alert output (5) · de-identification rule and de-identified zone (6) · access control and audit (7) · failure, replay and growth (8)", fill=LIGHT, edge=NAVY)
B.figure(f"{FG}/fig_task6_architecture.png", "Zone separation and stages of the fraud and sharing pipeline")
for (no, nm, f), c in zip(T6, [NAVY, NAVY, RED, TEAL, ORANGE, GREEN, GOLD, NAVY]): B.spec(no, nm, f, O6, c)
B.h2("Stage 5 – Desk-Check  |  1 Mark")
B.p("Window for Rule A = days d−6 to d. Rule B limit = 3 × median of earlier payments in the district.", keep=True)
B.grid(["Event", "Account (state A after update)", "Rule A", "District: earlier amounts → median; limit", "Rule B", "Flagged"],
 [["E1", "AC9: {B101} → 1", "no", "D1: none → skipped", "no", "—"],
  ["E2", "AC9: {B101, B102} → 2", "no", "D1: [2000] → 2000; 6000", "no", "—"],
  ["E3", "AC4: {B103} → 1", "no", "D2: none → skipped", "no", "—"],
  ["E4", "AC9: {B101, B102, B104} → **3**", "**YES**", "D1: [2000, 2000] → 2000; 6000", "no", "**Rule A**"],
  ["E5", "AC7: {B105} → 1", "no", "D2: [1500] → 1500; 4500. Amount **9000 > 4500**", "**YES**", "**Rule B**"],
  ["E6", "AC4: {B103, B106} → 2", "no", "D2: [1500, 9000] → 5250; 15750", "no", "—"],
  ["E7", "AC9 (day 9): B101 (day 1) and B102 (day 2) expire, leaving {B104, B107} → 2", "no", "D1: [2000, 2000, 2000] → 2000; 6000", "no", "—"],
  ["E8", "AC2: {B108} → 1", "no", "D1: [2000 ×4] → 2000; 6000. Amount 2100", "no", "—"]],
 [600, 2600, 700, 3000, 700, 1426], center=(0, 2, 4, 5))
B.callout("**E4 is flagged by Rule A** (account AC9 received payments for B101, B102 and B104 within days 1–3). **E5 is flagged by Rule B** (9000 is more than three times 1500, the only earlier amount in D2). No other event is flagged. E7 shows the discard rule at work: the old beneficiaries have left the 7-day window, so AC9 is no longer suspicious on day 9. E5's high amount raises the D2 median to 5250, so E6 passes; this shows that the median moves when an outlier is stored.", title="Result of the trace", fill="E8F5EE", edge=GREEN)
B.figure(f"{SS}/task6_fraud_trace_vscode_output.png", "VS Code output of task6_fraud_trace.py (E1–E8 trace and attack set X1–X7)", 6.2)
B.h2("Stage 6 – Attack Your Own Design  |  2 Marks")
B.p("**Attack set (7 events, new district D3).** Payments are split across four accounts that, in reality, one person controls, and amounts are kept just under the limit.", keep=True)
B.grid(["Event", "Beneficiary", "Account", "District", "Amount", "Day"],
 [["X1", "B301", "AC21", "D3", "1000", "1"], ["X2", "B302", "AC21", "D3", "1000", "2"], ["X3", "B303", "AC22", "D3", "1000", "3"],
  ["X4", "B304", "AC22", "D3", "1000", "4"], ["X5", "B305", "AC23", "D3", "1000", "5"], ["X6", "B306", "AC23", "D3", "2900", "6"],
  ["X7", "B307", "AC24", "D3", "2950", "6"]], [900, 1800, 1500, 1500, 1500, 1826], center=(0, 1, 2, 3, 4, 5))
B.kv([("(1) Why the input is challenging", "Rule A counts distinct beneficiaries **per account**, so spreading seven beneficiaries over four accounts keeps each account at one or two. Rule B uses a fixed multiple of the median, so amounts of 2,900 and 2,950 sit just below 3 × 1,000 = 3,000."),
      ("(2) Prediction before tracing", "**Nothing will be flagged.** Rule A will fail (no account reaches 3 distinct beneficiaries) and Rule B will fail (no amount exceeds 3,000)."),
      ("Trace", "Rule A counts: AC21 = 2, AC22 = 2, AC23 = 2, AC24 = 1. Rule B: median of earlier D3 payments is 1,000 at X2–X7, limit 3,000; X6 = 2,900 and X7 = 2,950 are both below it. First payment X1 skipped (no earlier payment)."),
      ("Conclusion", "**Both rules fail; prediction correct.** The critical decisions are the **grouping key of Rule A (Account)** and the **fixed 3 × threshold of Rule B**. The parts that do not fail: validation, de-duplication, zone separation, access control and audit are not affected by this attack.")])
B.p("**Release test (research data).** A district-week with only 4 payments forms a group smaller than k = 5, so Stage 6 suppresses or merges it; an attacker who knows a person's district, week and amount band therefore never sees fewer than 5 matching rows. Row numbers change on every release, so two releases cannot be joined.", "j")
B.callout("R1  Link accounts into clusters when they share an attribute (for example bank branch, phone or address, if added to the event) and apply Rule A to the cluster.\n"
          "R2  Add a lower watch threshold (for example 2 × the median) and a rule counting several payments between 2 × and 3 × within 30 days in one district; compare with peers of the same scheme.\n"
          "R3  Combine the rules into a risk score instead of independent yes/no flags.\n"
          "__These refinements are proposed only; they have not yet been written into the Pipeline Specification Template and were not traced.__", title="Proposed refinement", fill=CALL)

# ============================================================ INTERPRETATION, MATRIX, REPO
B.h1("INTERPRETATION, LIMITS AND RUBRIC COMPLIANCE")
B.h2("Critical decisions and limits of the designs")
B.grid(["Task", "Critical decision", "Limit of the design"],
 [["1", "Separating the identified zone from the de-identified zone and defining 'clean' as named checks", "Volumes, retention periods and k = 10 are assumptions; no hospital data was used"],
  ["2", "Windowing by event time with a watermark and a bounded allowed lateness", "The 5 s latency and state sizes are estimates, not measurements; very late events wait for the nightly batch"],
  ["3", "Taking the larger of the storage and scan node counts", "Assumes disks read in parallel and a scan of one replica; no allowance for growth beyond doubled imagery"],
  ["4", "Checking group size over combinations of quasi-identifiers, not only dropping columns", "k = 3 is for the demonstration; k-anonymity does not stop attacks using other outside knowledge"],
  ["5", "Carrying (sum, count) through the combiner; keeping data in memory across iterations", "Shuffle reduction (about 36,000×) and the 5 s budget are estimates"],
  ["6", "Choosing the grouping key (Account) and the threshold (3×) of the rules", "The two rules **fail** against split accounts and just-under-limit amounts; the refinement is proposed, not yet specified"]],
 [700, 4300, 4026], center=(0,))
B.h2("Rubric compliance matrix")
B.grid(["Task", "Rubric evidence expected", "Where it is answered", "Met"],
 [["1 (6)", "At least five deficiencies with reasons; complete repaired specification with a data-protection rule at each stage; defence ≤ 100 words", "Tasks 1.1 (8 deficiencies), 1.2 (6 stages, rule table), 1.3 (79 words)", "Yes"],
  ["2 (8)", "Problem model; stream/batch hypothesis; validation, de-duplication, watermark, windowing; 8-event decision trace; modified-case prediction", "Tasks 2.1–2.5 (model, one-sentence hypothesis, 7 stages, trace, E7 change)", "Yes"],
  ["3 (9)", "Quantity definitions; formulas with reasoning; storage and scan nodes; governing constraint; doubled imagery; dependency", "Tasks 3.1–3.5 (11 quantities, F1–F7, 12 steps, 4 → 7 nodes)", "Yes"],
  ["4 (7)", "Exact defect; own failing case with linkage trace; minimal repair to step 3; regression check", "Tasks 4.1–4.4 (quasi-identifiers, 7 records, step 3′, two regression cases)", "Yes"],
  ["5 (7)", "Key-value design with (sum, count) combiner; iteration cost; in-memory recovery; event time, watermark, lateness trade-off", "Tasks 5.1–5.3", "Yes"],
  ["6 (13)", "Abstraction without technology; strategy with rejected alternatives; state formulation; buildable specification; E1–E8 trace; attack on own design", "Stages 1–6 (governance stated separately, 3 options rejected, 8-stage specification, E4 by A and E5 by B, attack X1–X7)", "Yes"]],
 [800, 3600, 3926, 700], center=(0, 3))
B.h2("Submission contents (GitHub folder)")
B.p("The folder **CO4_Assignment4_BigData_Design** is organised as follows and is ready to upload to a GitHub repository:", keep=True)
B.grid(["Path", "Content"],
 [["README.md", "Purpose, folder map, how to run in VS Code, how to upload to GitHub"],
  ["docs/", "This Word document (editable)"],
  ["scripts/", "task1_spec_check.py to task6_fraud_trace.py and task1_spec_data.py; Python standard library only"],
  ["outputs/", "Captured text output of every script (the evidence behind each screenshot)"],
  ["screenshots/", "VS Code output screenshots used in Figures 2, 4, 6, 7, 9 and 11"],
  ["figures/ and tools/", "Diagrams used in the document and the programs that generate screenshots, figures and this document"]],
 [2200, 6826])
B.p("**Declaration.** This is my individual work. No big data framework, cluster or compiler was used to solve the tasks; the Python scripts only repeat arithmetic and manual traces for checking.", "j")

out = f"{ROOT}/docs/CSA15_Assignment4_PartI_Submission.docx"
doc.core_properties.title = "CSA15 Assignment 4 Part I - Big Data Solution Design Through Specification"
doc.save(out); print("saved", out, "figures:", B.fig)
