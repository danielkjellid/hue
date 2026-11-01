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

SRC  = src/hue_docs
DIST = dist
# Not 8000, which other local servers already use.
PORT ?= 8001

.PHONY: highlight-deps
highlight-deps: ; $(info $(M) installing Shiki) @
	$Q cd $(BASE)/$(SRC)/highlight && npm ci --silent

.PHONY: build-css
build-css: .venv ; $(info $(M) building css) @
	$Q cd $(BASE) && $(UV) run tailwindcss --minify \
		-i $(SRC)/styles/docs.input.css \
		-o $(DIST)/styles/tailwind.css

.PHONY: build
build: .venv build-css ; $(info $(M) freezing into $(DIST)/) @
	$Q test -d $(BASE)/$(SRC)/highlight/node_modules || $(MAKE) highlight-deps
	$Q cd $(BASE) && PYTHONPATH=src $(UV) run python -m hue_docs.freeze $(DIST)

# Live pages over a fresh build's stylesheet, scripts and search index.
# New Tailwind classes need another run, since nothing watches the CSS.
.PHONY: serve
serve: build ; $(info $(M) serving on http://localhost:$(PORT)) @
	$Q cd $(BASE) && PYTHONPATH=src $(UV) run uvicorn --factory \
		hue_docs.dev:app --reload --reload-dir src --port $(PORT)

# The Worker bundle: hue and the docs copied in beside the entry point, since
# Python Workers install only from PyPI. Caches are left behind.
.PHONY: worker
worker: ; $(info $(M) assembling the docs Worker) @
	$Q cd $(BASE)/worker/src && rm -rf hue hue_fastapi hue_docs
	$Q cd $(BASE) && rsync -a --exclude __pycache__ ../hue-python/src/hue worker/src/
	$Q cd $(BASE) && rsync -a --exclude __pycache__ ../hue-fastapi/src/hue_fastapi worker/src/
	$Q cd $(BASE) && rsync -a --exclude __pycache__ --exclude node_modules \
		--exclude highlight/package-lock.json $(SRC) worker/src/

# The Worker and the frozen site together, as Cloudflare would serve them.
.PHONY: preview
preview: build worker ; $(info $(M) previewing on http://localhost:$(PORT)) @
	$Q cd $(BASE)/worker && uv run pywrangler dev --port $(PORT)

########
# Test #
########

.PHONY: test
test: .venv ; $(info $(M) running tests) @
	$Q cd $(BASE) && $(UV) run pytest $(TESTS)
