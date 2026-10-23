PYTHON ?= python3
export PYTHONPATH := src

.PHONY: run verbose test artifacts docker

run:            ## Deliver the greeting (allow ~30 seconds for enterprise-grade latency)
	$(PYTHON) -m hwee

verbose:        ## Deliver the greeting while narrating every step to stderr
	$(PYTHON) -m hwee --verbose

test:           ## Run the quality assurance suite
	$(PYTHON) -m unittest discover -s tests -t . -v

artifacts:      ## Re-forge encoded artifacts: make artifacts GREETING="..."
	$(PYTHON) tools/forge_artifacts.py --greeting "$(GREETING)"

docker:
	docker build -t hwee:13.0.0 .
