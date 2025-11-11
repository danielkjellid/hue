PACKAGE = src/hue
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

.PHONY: watch-css
watch-css: .venv ; $(info $(M) watching css) @
	$Q $(UV) run tailwindcss -i $(PACKAGE)/static/styles/tailwind.input.css -o $(PACKAGE)/static/styles/tailwind.css --watch

.PHONY: build-css
build-css: .venv ; $(info $(M) building minified css) @
	$Q $(UV) run tailwindcss -i $(PACKAGE)/static/styles/tailwind.input.css -o $(PACKAGE)/static/styles/tailwind.css

.PHONY: copy-css-to-frameworks
copy-css-to-frameworks: copy-css-to-django

.PHONY: copy-css-to-django
copy-css-to-django: .venv ; $(info $(M) copying css to django) @
	$Q mkdir -p ../hue-django/src/hue_django/static/hue/styles
	$Q cp $(PACKAGE)/static/styles/tailwind.css ../hue-django/src/hue_django/static/hue/styles/tailwind.css


#########
# Build #
#########

.PHONY: build
build: build-css copy-css-to-frameworks
