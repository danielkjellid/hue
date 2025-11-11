PACKAGE = src/hue_django
BASE  	= $(shell dirname $(abspath $(firstword $(MAKEFILE_LIST))))
TESTS		= tests

include ../base.mk

.venv: pyproject.toml uv.lock ; $(info $(M) retrieving dependecies) @
	$Q test -d .venv || $(UV) venv .venv
	$Q $(UV) sync
	@touch .venv

#######
# CSS #
#######

.PHONY: check-css
check-css: ; $(info $(M) checking if django css matches hue-python css) @
	@if [ ! -f ../hue-python/src/hue/static/styles/tailwind.css ]; then \
		echo "Error: hue-python CSS file not found"; \
		exit 1; \
	fi; \
	if [ ! -f $(PACKAGE)/static/hue/styles/tailwind.css ]; then \
		echo "Error: Django CSS file not found"; \
		exit 1; \
	fi; \
	if diff -q ../hue-python/src/hue/static/styles/tailwind.css $(PACKAGE)/static/hue/styles/tailwind.css > /dev/null 2>&1; then \
		echo "Django CSS matches hue-python CSS"; \
		exit 0; \
	else \
		echo "Django CSS does not match hue-python CSS. Diff:"; \
		diff ../hue-python/src/hue/static/styles/tailwind.css $(PACKAGE)/static/hue/styles/tailwind.css || exit 1; \
	fi