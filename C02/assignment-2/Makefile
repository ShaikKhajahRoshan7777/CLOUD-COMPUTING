PY ?= python3

.PHONY: install test model demo analyze compare security image clean

install:            ## pip install -r requirements.txt
	$(PY) -m pip install -r requirements.txt

test:               ## unit tests (model maths + benchmark-output parsers)
	$(PY) -m unittest discover -s tests -v

model:              ## Tasks 3, 4, 6, 7 and 12 (pure maths - no special hardware needed)
	$(PY) scripts/task3_model.py
	$(PY) scripts/task4_conditions.py
	$(PY) scripts/task6_tradeoff.py
	$(PY) scripts/task6_tradeoff.py --peak 3 --external 30
	$(PY) scripts/task7_mitigations.py
	$(PY) scripts/task12_day4_redesign.py

image:              ## build the benchmark container image (Task 8)
	docker build -t educloud-bench:latest -f docker/Dockerfile.bench .

security:           ## Task 8 security validation
	$(PY) scripts/task8_security_validation.py

analyze:            ## Task 9 tables + graphs from data/results/results.csv
	$(PY) scripts/task9_analyze_results.py --machine "$(MACHINE)"

compare:            ## Task 10 theory vs experiment
	$(PY) scripts/task10_compare_theory_experiment.py

demo:               ## test the analysis pipeline on SYNTHETIC data (never report this data)
	$(PY) scripts/make_demo_data.py
	$(PY) scripts/task9_analyze_results.py --demo
	$(PY) scripts/task10_compare_theory_experiment.py --demo --cores 8

clean:
	rm -rf results/* data/demo/* __pycache__ */__pycache__
	touch results/.gitkeep data/demo/.gitkeep
