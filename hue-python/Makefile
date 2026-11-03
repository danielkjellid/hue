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
build-js: node_modules package.json ; $(info $(M) building js bundles) @
	$Q $(NPM) run build

#########
# Build #
#########

.PHONY: build
build: build-css build-js

.PHONY: dist
dist: build ; $(info $(M) building the wheel and sdist) @
	$Q cd $(BASE) && $(UV) build

# hue-django and hue-fastapi release in lockstep with hue-ui and pin it exactly,
# so one version moves all three. VERSION rather than V, which base.mk uses for
# verbosity.
.PHONY: version
version: ; $(info $(M) setting hue-ui, hue-django and hue-fastapi to $(VERSION)) @
	$Q test -n "$(VERSION)" || { echo "usage: make version VERSION=x.y.z"; exit 1; }
	$Q cd $(BASE) && $(UV) version -q $(VERSION)
	$Q for p in hue-django hue-fastapi; do \
		cd $(BASE)/../$$p && sed -i.bak 's/"hue-ui==[^"]*"/"hue-ui==$(VERSION)"/' pyproject.toml && rm pyproject.toml.bak \
		&& $(UV) version -q $(VERSION) || exit 1; \
	done
	$Q for p in hue-docs examples/django; do cd $(BASE)/../$$p && $(UV) lock -q || exit 1; done
