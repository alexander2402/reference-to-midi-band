PYTHON := .analysis-venv/bin/python

.PHONY: advise audit test validate native-preflight native-verify native-sync

advise:
	$(PYTHON) scripts/studio_pipeline.py advise

audit:
	$(PYTHON) scripts/audit_project.py

test:
	$(PYTHON) -m unittest discover -s tests -v

validate:
	$(PYTHON) scripts/validate_midis.py

native-preflight:
	$(PYTHON) scripts/garageband_native.py preflight

native-verify:
	$(PYTHON) scripts/garageband_native.py verify

native-sync:
	@test -n "$(HYPOTHESIS)" || (echo "HYPOTHESIS is required" && exit 2)
	@test -n "$(PRIMARY_CHANGE)" || (echo "PRIMARY_CHANGE is required" && exit 2)
	$(PYTHON) scripts/garageband_native.py sync \
		--hypothesis "$(HYPOTHESIS)" \
		--primary-change "$(PRIMARY_CHANGE)" \
		$(PROMOTE)
