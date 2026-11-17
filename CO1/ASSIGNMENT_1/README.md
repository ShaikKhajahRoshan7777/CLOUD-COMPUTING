# CSA15 - Cloud Computing and Big Data Analytics | Assignment 1 (CO1)
## Smart Campus Cloud Migration - supporting files

This folder holds everything that backs the Word report (`CSA15_CO1_Assignment_Report.docx`).

| Folder / file | Purpose (task) |
|---|---|
| `app/app.py` | Flask REST API proof-of-concept: result lookup, fee payment, library search, tenant isolation (Tasks 5, 9, 11) |
| `tests/test_api.py` | 10 automated functional tests, including the 404 failure case and the 403 tenant-isolation case (Task 9) |
| `tests/client_demo.py` | HTTP client that calls the running service and prints status + JSON (Task 9) |
| `Dockerfile`, `requirements.txt`, `.dockerignore` | Container build for the API (Tasks 4, 9) |
| `calculations/consolidation.py` | Server consolidation working: 12 servers -> hosts (Task 4) |
| `calculations/cost_model.py` | 3-year cost comparison (Task 10) |
| `calculations/availability_capacity.py` | 10x capacity, 99.9% availability and cost evidence (Task 11) |
| `calculations/make_diagrams.py` | Regenerates every figure in `diagrams/` |
| `diagrams/` | Timeline, virtualization, service layers, architecture (original + revised), cost, roadmap, availability |
| `screenshots/` | VS Code views of the code and of each program's output (S01-S12) |
| `logs/` | Raw text captured from each run |

## Reproduce (Windows / macOS / Linux)

```
python -m venv venv
venv\Scripts\activate            (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt

python app/app.py                      # terminal 1 - service on http://127.0.0.1:5000
python tests/client_demo.py            # terminal 2 - expect HTTP 200, 200, 404, 201, 200, 403
python -m unittest -v tests.test_api   # expect: Ran 10 tests ... OK

python calculations/consolidation.py
python calculations/cost_model.py
python calculations/availability_capacity.py
```

Quick checks with curl:
```
curl http://127.0.0.1:5000/api/v1/results/SIM2201001                      -> 200 JSON
curl http://127.0.0.1:5000/api/v1/results/SIM0000000                      -> 404 JSON
curl -X POST http://127.0.0.1:5000/api/v1/fees/payment -H "Content-Type: application/json" -d "{\"reg_no\":\"SIM2201001\",\"amount\":5000,\"mode\":\"UPI\"}"   -> 201
```

## Container (needs Docker Desktop)
```
docker build -t smart-campus-api .
docker run -d -p 5000:5000 --name campus-api smart-campus-api
curl http://localhost:5000/health
docker ps
```

## PaaS deployment (free tier, e.g. Render / Google Cloud Run / Azure App Service)
Build command: `pip install -r requirements.txt`   Start command: `gunicorn app.app:app`
Then open `https://<your-service-url>/health` and `/api/v1/results/SIM2201001`.

## Note on screenshots
Replace `screenshots/S01-S12` with captures taken on your own machine before final submission, and add the
Docker and PaaS screenshots (S13, S14) once you have run those two steps.
