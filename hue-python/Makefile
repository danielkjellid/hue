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

##############
# JavaScript #
##############

node_modules: package.json package-lock.json ; $(info $(M) installing js dependencies) @
	$Q $(NPM) install
	@touch node_modules

.PHONY: build-js
build-js: node_modules package.json ; $(info $(M) building js bundle) @
	$Q $(NPM) run build

#########
# Build #
#########

.PHONY: build
build: build-css build-js
