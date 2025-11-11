UV = uv

V = 0
Q = $(if $(filter 1,$V),,@)
M = $(shell printf "\033[34;1m▶\033[0m")

$(UV): ; $(info $(M) checking uv)
	$Q

$(BASE): | $(UV) ; $(info $(M) checking PROJECT)
	$Q

########
# Lint #
########

.PHONY: lint
lint: lint-mypy lint-ruff lint-ruff-format lint-deptry | $(BASE) ; @
	$Q

.PHONY: lint-ruff
lint-ruff: .venv | $(BASE) ; $(info $(M) running ruff lint...) @
	$Q cd $(BASE) && $(UV) run ruff check $(PACKAGE) $(TESTS)

.PHONY: lint-ruff-format
lint-ruff-format: .venv | $(BASE) ; $(info $(M) running ruff format...) @
	$Q cd $(BASE) && $(UV) run ruff format $(PACKAGE) $(TESTS) --diff

.PHONY: lint-mypy
lint-mypy: .venv | $(BASE) ; $(info $(M) running mypy...) @
	$Q cd $(BASE) && $(UV) run mypy --show-error-codes --show-column-numbers $(PACKAGE)

.PHONY: lint-deptry
lint-deptry: .venv | $(BASE) ; $(info $(M) running deptry...) @
	$Q cd $(BASE) && $(UV) run deptry $(BASE)

##########
# Fixers #
##########

.PHONY: fix
fix: fix-ruff fix-ruff-format | $(BASE) ; @
	$Q

.PHONY: fix-ruff
fix-ruff: .venv | $(BASE) ; $(info $(M) running ruff with fix...) @
	$Q cd $(BASE) && $(UV) run ruff check $(PACKAGE) $(TESTS) --fix

.PHONY: fix-ruff-format
fix-ruff-format: .venv | $(BASE) ; $(info $(M) running ruff format with fix...) @
	$Q cd $(BASE) && $(UV) run ruff format $(PACKAGE) $(TESTS)