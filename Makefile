PYTHON ?= python
.PHONY: reproduce finish verify test manuscript
reproduce manuscript:
	$(PYTHON) scripts/55_complete_study.py
finish:
	$(PYTHON) scripts/55_complete_study.py --finish-experiments
verify:
	$(PYTHON) scripts/16_verify_results.py
test:
	$(PYTHON) -m pytest -q tests
