---
description: Quality gate — run lint + tests for the package(s) you changed
---

Run the quality gate before finishing work.

1. Determine which package(s) have uncommitted changes (`git status --short`): `hue-python/`,
   `hue-docs/`, and/or `hue-django/`.
2. For each changed package, `cd` into it and run:
   - `make lint` (ruff check + ruff format --diff + mypy + deptry)
   - tests: `uv run pytest tests` for `hue-python`/`hue-django`, or `make test` for `hue-docs`
3. Report failures grouped by package. If `ruff` reports formatting or fixable lint issues,
   offer to run `make fix`. If mypy or tests fail, fix the root cause rather than suppressing.
4. If nothing changed in a package, skip it. If nothing changed at all, run the `hue-python`
   gate as the default.
