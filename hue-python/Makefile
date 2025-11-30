PACKAGE = src/hue
BASE  	= $(shell dirname $(abspath $(firstword $(MAKEFILE_LIST))))
TESTS		= tests
NPM 		= npm

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
	$Q $(UV) run tailwindcss -i $(PACKAGE)/static/styles/tailwind.input.css -o ../hue-django/src/hue_django/static/hue/styles/tailwind.css --minify
	
.PHONY: copy-js
copy-js: build-js package.json ; $(info $(M) copying js bundle to django) @
	$Q cp $(PACKAGE)/static/js/alpine-bundle.js ../hue-django/src/hue_django/static/hue/js/alpine-bundle.js

.PHONY: build-js
build-js: package.json ; $(info $(M) building js bundle) @
	$Q $(NPM) run build


.PHONY: check-css
check-css: .venv ; $(info $(M) checking if css would change) @
	$Q $(UV) run tailwindcss -i $(PACKAGE)/static/styles/tailwind.input.css -o /tmp/tailwind.css
	@if diff -q $(PACKAGE)/static/styles/tailwind.css /tmp/tailwind.css > /dev/null 2>&1; then \
		echo "No changes would be made"; \
		exit 0; \
	else \
		echo "CSS would change. Diff:"; \
		diff $(PACKAGE)/static/styles/tailwind.css /tmp/tailwind.css || exit 1; \
	fi

#########
# Build #
#########

.PHONY: build
build: build-css build-js copy-js
