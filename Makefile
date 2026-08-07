PYTHON := .analysis-venv/bin/python
PROJECT ?= gorodok
PROJECT_ENV := STUDIO_PROJECT=$(PROJECT)

.PHONY: advise audit test validate native-preflight native-verify native-sync new-project history history-show history-checkpoint

advise:
	$(PROJECT_ENV) $(PYTHON) scripts/studio_pipeline.py advise

audit:
	$(PROJECT_ENV) $(PYTHON) scripts/audit_project.py

test:
	$(PROJECT_ENV) $(PYTHON) -m unittest discover -s tests -v

validate:
	$(PROJECT_ENV) $(PYTHON) scripts/validate_midis.py

native-preflight:
	$(PROJECT_ENV) $(PYTHON) scripts/garageband_native.py preflight

native-verify:
	$(PROJECT_ENV) $(PYTHON) scripts/garageband_native.py verify

native-sync:
	@test -n "$(HYPOTHESIS)" || (echo "HYPOTHESIS is required" && exit 2)
	@test -n "$(PRIMARY_CHANGE)" || (echo "PRIMARY_CHANGE is required" && exit 2)
	$(PROJECT_ENV) $(PYTHON) scripts/garageband_native.py sync \
		--hypothesis "$(HYPOTHESIS)" \
		--primary-change "$(PRIMARY_CHANGE)" \
		$(PROMOTE)

new-project:
	@test -n "$(NAME)" || (echo "NAME is required" && exit 2)
	$(PYTHON) scripts/new_project.py "$(NAME)"

history:
	$(PROJECT_ENV) $(PYTHON) scripts/project_history.py list

history-show:
	@test -n "$(REVISION)" || (echo "REVISION is required" && exit 2)
	$(PROJECT_ENV) $(PYTHON) scripts/project_history.py show "$(REVISION)"

history-checkpoint:
	@test -n "$(LABEL)" || (echo "LABEL is required" && exit 2)
	@test -n "$(SUMMARY)" || (echo "SUMMARY is required" && exit 2)
	$(PROJECT_ENV) $(PYTHON) scripts/project_history.py checkpoint \
		--label "$(LABEL)" \
		--summary "$(SUMMARY)" \
		$(if $(AUTHOR),--author "$(AUTHOR)") \
		$(if $(TAG),--tag "$(TAG)")
