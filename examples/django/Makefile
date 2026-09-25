PACKAGE = example
BASE  	= $(shell dirname $(abspath $(firstword $(MAKEFILE_LIST))))
TESTS		= tests

include ../../base.mk

.venv: pyproject.toml uv.lock ; $(info $(M) retrieving dependecies) @
	$Q test -d .venv || $(UV) venv .venv
	$Q $(UV) sync
	@touch .venv

# hue serves a stylesheet that is generated rather than committed, so a fresh
# checkout builds it once before the first page is drawn.
.PHONY: css
css: ; $(info $(M) building hue's stylesheet...) @
	$Q cd ../../hue-python && $(MAKE) --no-print-directory build-css

.PHONY: db
db: .venv ; $(info $(M) migrating and seeding the database...) @
	$Q cd $(BASE) && $(UV) run python manage.py migrate --verbosity 0
	$Q cd $(BASE) && $(UV) run python manage.py seed

.PHONY: serve
serve: .venv css db ; $(info $(M) serving on http://localhost:8001/billing/) @
	$Q cd $(BASE) && $(UV) run python manage.py runserver 8001

.PHONY: test
test: .venv ; $(info $(M) running tests...) @
	$Q cd $(BASE) && $(UV) run pytest $(TESTS)
