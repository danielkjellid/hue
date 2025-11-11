PACKAGE = hue
BASE  	= $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
TESTS		= tests

UV      = uv

V = 0
Q = $(if $(filter 1,$V),,@)
M = $(shell printf "\033[34;1m▶\033[0m")

$(UV): ; $(info $(M) checking uv)
	$Q

$(BASE): | $(UV) ; $(info $(M) checking PROJECT)
	$Q

.venv: pyproject.toml uv.lock | $(BASE) ; $(info $(M) retrieving dependecies) @
	$Q cd $(BASE) && $(UV) pip install -U pip
	$Q cd $(BASE) && $(UV) sync
	@touch $@

#######
# CSS #
#######

.PHONY: watch-css
watch-css: .venv | $(BASE) ; $(info $(M) watching css) @
	$Q cd $(BASE) && $(UV) run tailwindcss -i ./src/$(PACKAGE)/static/styles/tailwind.input.css -o ./src/$(PACKAGE)/static/styles/tailwind.css --watch

.PHONY: build-css
build-css: .venv | $(BASE) ; $(info $(M) building minified css) @
	$Q cd $(BASE) && $(UV) run tailwindcss -i ./src/$(PACKAGE)/static/styles/tailwind.input.css -o ./src/$(PACKAGE)/static/styles/tailwind.css

.PHONY: copy-css-to-frameworks
copy-css-to-frameworks: copy-css-to-django


.PHONY: copy-css-to-django
copy-css-to-django: .venv | $(BASE) ; $(info $(M) copying css to django) @
	$Q mkdir -p ../hue-django/src/hue_django/static/hue/styles
	$Q cp ./src/$(PACKAGE)/static/styles/tailwind.css ../hue-django/src/hue_django/static/hue/styles/tailwind.css


#########
# Build #
#########

.PHONY: build
build: build-css copy-css-to-frameworks
