PACKAGE = src/hue_docs src/hue_docs_v2
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

# CSS_OUT so the tests can build a throwaway copy without touching dist/.
CSS_OUT ?= dist/styles/tailwind.css

.PHONY: build-css
build-css: .venv ; $(info $(M) building docs css) @
	$Q cd $(BASE) && $(UV) run tailwindcss \
		-i src/hue_docs/styles/docs.input.css \
		-o $(CSS_OUT)

.PHONY: watch-css
watch-css: .venv ; $(info $(M) watching docs css) @
	$Q cd $(BASE) && $(UV) run tailwindcss \
		-i src/hue_docs/styles/docs.input.css \
		-o dist/styles/tailwind.css --watch

.PHONY: serve
serve: ; $(info $(M) serving dist/ on http://localhost:8000) @
	$Q cd $(BASE)/dist && python3 -m http.server 8000

.PHONY: clean
clean: ; $(info $(M) removing dist/) @
	$Q rm -rf $(BASE)/dist

###########
# Docs v2 #
###########

V2      = src/hue_docs_v2
DIST_V2 = dist-v2
# Not 8000, which v1's serve and other local servers already use.
PORT_V2 ?= 8001

.PHONY: highlight-deps
highlight-deps: ; $(info $(M) installing Shiki) @
	$Q cd $(BASE)/$(V2)/highlight && npm ci --silent

.PHONY: build-css-v2
build-css-v2: .venv ; $(info $(M) building docs v2 css) @
	$Q cd $(BASE) && $(UV) run tailwindcss --minify \
		-i $(V2)/styles/docs.input.css \
		-o $(DIST_V2)/styles/tailwind.css

.PHONY: build-v2
build-v2: .venv build-css-v2 ; $(info $(M) freezing docs v2 into $(DIST_V2)/) @
	$Q test -d $(BASE)/$(V2)/highlight/node_modules || $(MAKE) highlight-deps
	$Q cd $(BASE) && PYTHONPATH=src $(UV) run python -m hue_docs_v2.freeze $(DIST_V2)

# Live pages over a fresh build's stylesheet, scripts and search index.
# New Tailwind classes need another run, since nothing watches the CSS.
.PHONY: serve-v2
serve-v2: build-v2 ; $(info $(M) serving docs v2 on http://localhost:$(PORT_V2)) @
	$Q cd $(BASE) && PYTHONPATH=src $(UV) run uvicorn --factory \
		hue_docs_v2.dev:app --reload --reload-dir src --port $(PORT_V2)

# The Worker bundle: hue and the docs copied in beside the entry point, since
# Python Workers install only from PyPI. Caches are left behind.
.PHONY: worker-v2
worker-v2: ; $(info $(M) assembling the docs Worker) @
	$Q cd $(BASE)/worker/src && rm -rf hue hue_fastapi hue_docs_v2
	$Q cd $(BASE) && rsync -a --exclude __pycache__ ../hue-python/src/hue worker/src/
	$Q cd $(BASE) && rsync -a --exclude __pycache__ ../hue-fastapi/src/hue_fastapi worker/src/
	$Q cd $(BASE) && rsync -a --exclude __pycache__ --exclude node_modules \
		--exclude highlight/package-lock.json $(V2) worker/src/

# The Worker and the frozen site together, as Cloudflare would serve them.
.PHONY: preview-v2
preview-v2: build-v2 worker-v2 ; $(info $(M) previewing on http://localhost:$(PORT_V2)) @
	$Q cd $(BASE)/worker && uv run pywrangler dev --port $(PORT_V2)

########
# Test #
########

.PHONY: test
test: .venv ; $(info $(M) running tests) @
	$Q cd $(BASE) && $(UV) run pytest $(TESTS)
