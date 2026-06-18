PACKAGE = src/hue_docs
BASE    = $(shell dirname $(abspath $(firstword $(MAKEFILE_LIST))))
TESTS   = tests

include ../base.mk

.venv: pyproject.toml ; $(info $(M) retrieving dependencies) @
	$Q test -d .venv || $(UV) venv .venv
	$Q $(UV) sync
	@touch .venv

#########
# Build #
#########

.PHONY: build
build: .venv ; $(info $(M) building docs site into dist/) @
	$Q cd $(BASE) && PYTHONPATH=src $(UV) run python -m hue_docs

.PHONY: watch-css
watch-css: .venv ; $(info $(M) watching docs css) @
	$Q cd $(BASE) && $(UV) run tailwindcss \
		-i $(PACKAGE)/styles/docs.input.css \
		-o dist/styles/tailwind.css --watch

.PHONY: serve
serve: ; $(info $(M) serving dist/ on http://localhost:8000) @
	$Q cd $(BASE)/dist && python3 -m http.server 8000

.PHONY: clean
clean: ; $(info $(M) removing dist/) @
	$Q rm -rf $(BASE)/dist

########
# Test #
########

.PHONY: test
test: .venv ; $(info $(M) running tests) @
	$Q cd $(BASE) && $(UV) run pytest $(TESTS)
