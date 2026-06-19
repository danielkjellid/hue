# Hue — working notes for Claude

Hue is a component library for Python that renders HTML. Components are written in a
declarative, chainable style and rendered with [`htmy`](https://pypi.org/project/htmy/);
styling is Tailwind; interactivity is Alpine.js + Alpine AJAX.

## Repo shape

Three packages, each independently managed by `uv` with its **own `.venv`**. This is **not**
a uv workspace — `hue-docs` and `hue-django` depend on `hue` via editable path installs
(`hue = { path = "../hue-python", editable = true }`). A shared `ruff.toml` and `base.mk`
live at the repo root.

| Package | Path | What it is |
| --- | --- | --- |
| `hue` | `hue-python/` | The core library — components, renderer, router, utils |
| `hue-docs` | `hue-docs/` | Static-site generator that auto-discovers and showcases components |
| `hue-django` | `hue-django/` | Django integration (views, router, asset middleware) |

**Always run tooling from inside the relevant package directory** (the Makefiles `cd` into
`$(BASE)` themselves, but `uv run …` does not).

## Commands

Run from the package directory. `make lint`/`make fix` exist in every package (via
`base.mk`); other targets vary.

```bash
# Lint (ruff check + ruff format --diff + mypy + deptry)   — any package
make lint
# Autofix (ruff check --fix + ruff format)                 — any package
make fix

# Tests
uv run pytest tests          # hue-python and hue-django (no make target)
make test                    # hue-docs only

# Docs (from hue-docs/)
PYTHONPATH=src uv run python -m hue_docs   # build → writes dist/   (also: make build)
make serve                                 # http.server on http://localhost:8000

# Assets (from hue-python/)
make build        # build CSS + JS, copy bundles into hue-django/.../static/hue/
make watch-css    # Tailwind watch mode
```

Before finishing any change, run `make lint` (and the relevant tests) — or use `/check`.

## The chainable-component pattern

Every UI element subclasses `ChainableComponent`
(`hue-python/src/hue/ui/base.py`). Read `atoms/button.py` and `molecules/callout.py` as the
canonical templates. The shape:

- State lives in `self._props`, `self._attrs`, and `self._children`.
- Each modifier method sets a prop/attr and **returns `self`** so calls chain:
  `Button().variant("primary").size("md").content(Text("Save"))`.
- Children are passed positionally or via `.content(*children)`.
- The subclass implements `_render(self, context: HueContext) -> Component`: read props with
  `self._get_prop(key, default)`, splat shared attrs with `self._get_base_html_attrs()`, and
  return an `htmy.html.*` tree.
- Variants/sizes/shapes are PEP 695 type aliases: `type ButtonVariant = Literal[...]`.
- `category: ClassVar[str]` sets the docs sidebar group (e.g. `"Actions"`, `"Feedback"`).
- `@classmethod example(cls) -> Self` returns a representative instance for the docs preview.
- The base already provides `.class_()`, `.id()`, the ARIA helpers (`aria_label`, `role`,
  `aria_expanded`, …), and the Alpine / Alpine AJAX directives — **reuse them**, don't
  re-add per component.
- Build Tailwind class strings with the helpers in `hue-python/src/hue/utils.py`
  (see below). Export every new component from `hue-python/src/hue/ui/__init__.py`
  (add the import *and* the alphabetized `__all__` entry).

### Utilities (`hue-python/src/hue/utils.py`) — reuse these

- `classnames(*args)` — join `str | list[str] | dict[str, bool] | None` into a class string
  (falsy/`None` dropped).
- `classes_if(condition, classes)` — `{cls: condition}` for every class; use for a block of
  classes gated on one condition.
- `classes_if_else(condition, if_true, if_false)` — mutually-exclusive class sets.
- `render_if(value, factory, fallback=UNDEFINED)` — render `factory(value)` when `value` is
  not `None`, else `fallback` (renders nothing by default). Use for optional children.

## Docs auto-discovery (don't break it)

`hue-docs` introspects `hue.ui.__all__`, keeps `ChainableComponent` subclasses, derives
"axes" from `Literal` enum and `bool` modifier signatures, and reads default values out of
`_render` source by regex-matching `_get_prop("name", <default>)`. Practical rules so a new
component shows up correctly:

- Keep the `example()` body a **single simple expression** — it is AST-unparsed into the
  snippet shown on the site.
- Use real `Literal` type aliases for variant axes (so they resolve as enum axes).
- Defaults must be **literals written inside** the `_get_prop(...)` call, not computed
  elsewhere.
- `hue-docs` pins `htmy==0.8.2` (APIs removed in 0.9+); keep core compatible with that pin.

## Testing

Tests live in each package's `tests/`. In `hue-python`, there is **one test file per
component** under `tests/components/`, shared fixtures in `tests/conftest.py`, and shared
accessibility helpers in `tests/_a11y.py`.

**Mechanics:** use the `context_args` fixture (a `HueContextArgs` with a mock request), then
`await render_tree(component, context_args=context_args)` (mark the test
`@pytest.mark.asyncio`) and assert against the returned HTML — preferably via the `_a11y.py`
parse helpers rather than brittle substring checks.

**Philosophy — test the concepts, not exhaustively.** The current suite has been trimmed; do
not regrow it. For each component cover what actually matters:

- That each variant renders as expected (e.g. `Callout().variant("error")` produces the
  error styling/markup).
- That key props change the output, and required structure/attributes are present.
- That **accessibility invariants hold** (semantic element, expected `role`/`aria-*`, labels
  associated with inputs, decorative icons `aria-hidden`, focusable where applicable).
- **Conditional rendering both ways.** Any branch — `render_if`/`render_if_else`,
  `classes_if`/`classes_if_else`, or a plain `if` in `_render` (title shown vs omitted,
  disabled vs enabled, child present vs absent) — gets an isolated unit test for **each**
  branch: one proving the element/class appears when the condition holds, one proving it is
  absent when it doesn't.

Do **not** write ~25 trivial tests per component, and do **not** re-test the shared
`ChainableComponent` modifiers per component — those are tested once in `tests/test_base.py`.

Accessibility assertions parse the rendered HTML (helpers in `tests/_a11y.py`, built on
`beautifulsoup4`). The heavier `axe-playwright-python` WCAG engine needs a headless browser
and is intentionally not used here.

## Component quality bar

Every component must satisfy these — review against them before finishing:

- **Accessibility first (hard requirement).** Prefer semantic HTML over `div` soup; wire up
  the ARIA helpers already on the base; ensure keyboard operability and visible focus
  (`focus-visible:outline…`, see `Button`); associate labels with inputs; use live regions /
  `aria-hidden` appropriately. When unsure, pick the most accessible established pattern
  (cross-check WAI-ARIA Authoring Practices) and say so.
- **Backwards compatible.** Additive changes only to existing components — don't rename/drop
  modifier methods, change defaults, or alter rendered structure in ways that break current
  usage. Flag any unavoidable break explicitly.
- **Declarative & simple API.** Usage should read as `Component().variant(…).content(…)`.
  Keep the public surface small and obvious.
- **DRY, but earn the abstraction.** Reuse existing components and utils. A new util must be
  used in **≥2 places** — otherwise inline it. Watch for brittle, drift-prone coupling (e.g.
  the docs' regex/AST reading of `example()` and `_get_prop` defaults — keep those shapes
  conventional).
- **No over-complicated Tailwind.** Keep class lists readable; lean on `classnames` /
  `classes_if`; don't hand-roll deep conditional class soup.
- **Comments & docstrings:** informative and simple — explain *why*, not *what*. Don't
  over-document. Write docstrings as **plain prose**: no reStructuredText markup (no
  ``` ``backticks`` ```, no `:func:`/`:class:`/`:data:` roles, no `::` literal blocks) — refer
  to code in plain words (`size-4`, `aria-hidden`, `create_icon_base`). State the *why* and any
  one nuance worth keeping; drop exhaustive lists, restated signatures, and repeated examples.
  At most one short example, and only when it earns its place. Always start a docstring on a
  new line after the opening `"""` (summary on the second line), including one-line docstrings.
- Priority order: **correctness → performance → readability/reusability.**

### Building from a React reference

The user will often paste a component from a React library as the visual/behavioral
reference. Mimic its look and API intent, but **re-express it in the chainable `htmy`
idiom** (not a 1:1 port) and **upgrade its accessibility** to meet the bar above rather than
copying whatever the reference happens to do. Map the reference's props to chainable modifier
methods and its variants to `Literal` axes.

## Django integration (`hue-django/src/hue_django/`)

- `HueView` — full-page view; define `index(self, request, context) -> BasePage` (sync or
  async) and an optional `router`. Exposes `.urls` / `.app_name` as class properties.
- `HueFragmentsView` — router-only view (no `index`).
- `Router[HttpRequest]` (`router.py`) — `@router.fragment_post("path/<int:id>/")`; parses
  Django path params, injects the CSRF token into `HueContextArgs`, detects AJAX
  (`X-Requested-With` / `X-Alpine-Request`), and wraps sync handlers in `sync_to_async`.
- `HueAssetsMiddleware` (`middleware.py`) — serves `/__hue__/styles.css` and
  `/__hue__/js/alpine.js` straight from the `hue` package (no `collectstatic`), with ETag
  caching.
- Tests configure Django in `conftest.py` and use the `urlpatterns_` fixture for isolation.

## House rules

- Run `make lint` (or `/check`) before finishing.
- No relative imports across parent packages (`ban-relative-imports = "parents"`).
- Start component files with `from __future__ import annotations`.
