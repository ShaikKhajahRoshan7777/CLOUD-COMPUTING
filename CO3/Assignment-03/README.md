# CSA15 - Cloud Computing and Big Data Analytics | Assignment 3 (CO3)

Cloud-based access, Web APIs, security and collaboration - SIMATS Engineering, Department of Information Technology.

## What is in this repository
| Folder / file | Purpose |
|---|---|
| `src/q3_api_client.py` | Q3 - Python client that calls the public PyPI JSON Web API (2 valid inputs + 1 invalid) |
| `src/q4_auth_demo.py` | Q4 - authentication (PBKDF2), signed expiring token (HMAC), role-based authorisation, attack simulations |
| `src/cloud_collab.py` | Q5-Q7 - collaboration engine: sharing, roles, versions, conflict detection, audit log |
| `src/q6_assignment_portal.py` | Q6 - assignment submission and evaluation prototype (2 user scenarios) |
| `src/q7_validation_tests.py` | Q7 - 9 test cases, expected vs observed |
| `outputs/` | Captured real terminal output of every program |
| `screenshots/` | VS Code style execution screenshots used in the report |
| `diagrams/` | Architecture and flow diagrams |
| `tools/` | Scripts that generated the diagrams, screenshots and the Word report |
| `docs/` | Final Word report (with the editable evaluation form on pages 1-2) |

## How to run (VS Code)
```bash
python -m venv .venv
.venv\Scripts\activate            # Windows   (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
python src/q3_api_client.py       # needs Internet
python src/q4_auth_demo.py
python src/q6_assignment_portal.py
python src/q7_validation_tests.py
```
Take your own screenshots of each run with `Win + Shift + S` (the images in `screenshots/` are rendered from the real source and real output and can be replaced).

## Upload to GitHub
```bash
git init
git add .
git commit -m "CO3 Assignment 3 - cloud access, API, security, collaboration"
git branch -M main
git remote add origin https://github.com/<your-username>/cloud_co3_assignment.git
git push -u origin main
```
