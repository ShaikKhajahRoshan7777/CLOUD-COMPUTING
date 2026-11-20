# CSA15 – Cloud Computing and Big Data Analytics
## Assignment 4 – Part I: Big Data Solution Design Through Specification (CO4)

Design-only assignment: every solution is written in the **Pipeline Specification Template**
(INPUT, PROCESS, OUTPUT, STORAGE, LATENCY, SECURITY). The Python scripts only **check the arithmetic and
repeat the manual desk-checks**; they are not a substitute for the specifications in the Word document.

## Folder map
| Path | Content |
|---|---|
| `docs/CSA15_Assignment4_PartI_Submission.docx` | Editable submission (pages 1-4 = original sheets, answers from page 5) |
| `scripts/` | `task1_spec_check.py` ... `task6_fraud_trace.py` (+ `task1_spec_data.py`), standard library only |
| `outputs/` | Captured text output of every script |
| `screenshots/` | VS Code output screenshots used in the document |
| `figures/` | Diagrams used in the document |
| `tools/` | Programs that generate the screenshots, figures and the Word file |

## Results at a glance
| Task | Check | Result |
|---|---|---|
| 1 | 6 stages x 6 fields, protection rule per stage, defence words | all pass, 79 words |
| 2 | 8-event trace | E3 merged, E4/E5 rejected, E7 late-accepted; E7 = 52 gives 44.0 |
| 3 | Sizing | 2.88 GB/day, 220.05 TB, 4 nodes (storage governs); imagery doubled = 7 nodes |
| 4 | Linkage attack | 4 of 5 people re-identified; after repair 3-4 candidates each |
| 5 | MapReduce sample | R7 = 45.0, R9 = 50.0 (naive average of averages = 51.88) |
| 6 | E1-E8 and attack X1-X7 | E4 by Rule A, E5 by Rule B; attack set flags nothing |

## Run in VS Code
1. Open this folder (File > Open Folder). Install the Python extension; Python 3.9+.
2. Open a script in `scripts/`, open the terminal (Ctrl+`) and run, for example:
   ```
   cd scripts
   python task3_sizing.py
   ```
3. Take the screenshot of the editor + terminal (Win+Shift+S) and save it in `screenshots/`.
   (The screenshots supplied here were rendered from the real captured output; replace them with your own captures if required.)

## Upload to GitHub
```
git init
git add .
git commit -m "CO4 Assignment 4 Part I - big data solution design"
git branch -M main
git remote add origin https://github.com/<your-username>/CO4_Assignment4_BigData_Design.git
git push -u origin main
```
(Or on github.com: New repository > Upload files > drag this whole folder's contents.)
