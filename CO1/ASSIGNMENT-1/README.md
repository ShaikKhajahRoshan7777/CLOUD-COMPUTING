# Smart Campus Cloud Migration - CSA15 Assignment 1 (CO1)

**Course:** CSA15 - Cloud Computing and Big Data Analytics
**Student:** SHAIK KHAJAH ROSHAN  |  **Program:** B.Tech CSE  |  **Faculty:** Sangeetha
**Topic:** Design, Analyse and Validate a Cloud-Based Solution for Migrating a Legacy University Management System

This repository holds the code and supporting files for the assignment: a Dockerised
Flask REST API (Task 9 proof-of-concept) plus Python scripts that reproduce the
calculations in Tasks 4, 10 and 11, and generate the report figures.

> Cost figures, capacity numbers and endpoints are **planning assumptions** for an academic
> design, not provider quotations. Screenshots in `screenshots/` must be your own.

## Folder structure

```
university-cloud-migration/
├── app.py                      # Flask REST API (3 university web services)
├── Dockerfile                  # container image for the API
├── docker-compose.yml          # one-command run: docker compose up --build
├── requirements.txt            # runtime dependencies
├── requirements-dev.txt        # + matplotlib, pytest
├── calculations/
│   ├── server_consolidation.py # Task 4  - 12 servers -> 3 hosts (4 with N+1)
│   ├── cost_comparison.py      # Task 10 / 11.8 - 3-year cost in INR
│   ├── capacity_availability.py# Task 11 - 99.9% downtime, 10x load sizing
│   └── generate_diagrams.py    # builds PNG figures into docs/figures/
├── tests/
│   └── test_api.py             # 13 unit tests (API + calculations)
├── docs/
│   ├── CO1-ASSIGNMENT_QUESTIONS.docx
│   ├── CO1-ASSIGNMENT_ANSWERS.docx
│   └── figures/                # evolution, architecture, service models, cost
└── screenshots/                # put YOUR Task 9 screenshots here
```

## API endpoints (Task 5 / Task 9)

| Function | Method | Endpoint |
| --- | --- | --- |
| Home / check | GET | `/` |
| Health check | GET | `/health` |
| Result lookup | GET | `/api/v1/students/<student_id>/results` |
| Fee payment (demo) | POST | `/api/v1/payments` |
| Library search | GET | `/api/v1/library/books?query=cloud&campus=MAIN` |

## Run with Docker (Task 9)

```bash
docker build -t university-api .
docker run --name university-api-container -p 5000:5000 university-api
```
or: `docker compose up --build`

## Test the API (second terminal)

```bash
curl http://localhost:5000/
curl http://localhost:5000/api/v1/students/STU1024/results          # 200
curl -i http://localhost:5000/api/v1/students/UNKNOWN/results       # 404
curl -X POST http://localhost:5000/api/v1/payments \
     -H "Content-Type: application/json" \
     -d '{"studentId":"STU1024","amount":12500,"currency":"INR","paymentRef":"FEE-2026-1024"}'
curl "http://localhost:5000/api/v1/library/books?query=cloud&campus=MAIN"
```

## Run without Docker

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python app.py
```

## Run the calculations and tests

```bash
python calculations/server_consolidation.py
python calculations/cost_comparison.py
python calculations/capacity_availability.py
python calculations/generate_diagrams.py
python -m unittest discover -s tests -v
```

## Screenshots to capture for Task 9 (save in `screenshots/`)

1. Project folder showing `app.py`, `requirements.txt`, `Dockerfile`
2. `docker build` finishing successfully
3. `docker ps` showing the running container
4. `curl` / browser output for `/`
5. Valid student result (HTTP 200)
6. Unknown student (HTTP 404)
7. PaaS deployment dashboard + live URL (if you deploy)

Also note your OS, Docker and Python versions, and the date.

## Optional: deploy to a PaaS (Task 9.4)

The same container can be deployed to Azure App Service, Google Cloud Run / App Engine or
AWS Elastic Beanstalk using the provider's free tier. Record the service, region and plan you used.
