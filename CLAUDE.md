# Hue — working notes for Claude

Hue is a component library for Python that renders HTML. Components are written in a
declarative, chainable style and rendered with [`htmy`](https://pypi.org/project/htmy/);
styling is Tailwind; interactivity is Alpine.js + Alpine AJAX.

## Repo shape

Four packages, each independently managed by `uv` with its **own `.venv`**. This is **not**
a uv workspace: `hue-docs`, `hue-django` and `hue-fastapi` depend on `hue` via editable path installs
(`hue = { path = "../hue-python", editable = true }`). A shared `ruff.toml` and `base.mk`
live at the repo root.

| Package | Path | What it is |
| --- | --- | --- |
| `hue` | `hue-python/` | The core library — components, renderer, router, utils |
| `hue-docs` | `hue-docs/` | Static-site generator that auto-discovers and showcases components |
| `hue-django` | `hue-django/` | Django integration (views, router, asset middleware) |
| `hue-fastapi` | `hue-fastapi/` | FastAPI integration (views, router, CSRF, asset routes) |

**Always run tooling from inside the relevant package directory** (the Makefiles `cd` into
`$(BASE)` themselves, but `uv run …` does not).

## Commands

Run from the package directory. `make lint`/`make fix` exist in every package (via
`base.mk`); other targets vary.

**`hue-python/src/hue/static/styles/tailwind.css` is generated, not committed.** Build it
with `make build-css` in `hue-python`. The test suites build it for you when it is missing,
so a fresh checkout needs nothing special; `read_css()` says the same if anything else hits
it first. Never commit it: a generated file in every branch is a conflict in every branch,
which is why it left the repo. The JS bundles stay committed by contrast (the Alpine bundle
and `chart-bundle.js`, the chart library it fetches on demand), because building them needs
npm while the Tailwind CLI arrives with hue's own dependencies.

**Building a distribution**: `make dist` in `hue-python` (not bare `uv build`). The
stylesheet and the JS bundles are generated, so a wheel built without them installs
as a component library that styles nothing — a build hook (`hue-python/hatch_build.py`)
refuses to produce one, and `tests/test_distribution.py` asserts what a consumer
actually receives.

```bash
# Lint (ruff check + ruff format --diff + mypy + deptry)   — any package
make lint
# Autofix (ruff check --fix + ruff format)                 — any package
make fix

# Tests
uv run pytest tests          # hue-python, hue-django and hue-fastapi (no make target)
make test                    # hue-docs only

# Docs (from hue-docs/)
make build                                 # build → writes dist/ (pins the Tailwind version)
make serve                                 # http.server on http://localhost:8000

# Assets (from hue-python/)
make build        # build CSS + the Alpine JS bundle (hue-django serves them from the hue package)
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
- **Three values or more for a `Literal`, or it is a boolean modifier named after the
  one thing that is not the default.** An axis with exactly two values makes a caller
  say the default out loud to discover there was one, and the default's name is then a
  string nobody ever writes: `Tabs().segmented()`, `Badge().pill()`, `Avatar().square()`,
  `Stack().horizontal()`, and a row that is not segmented says nothing at all. Two axes
  stay a `Literal` however short they are, because they are shared vocabulary rather
  than one component's own choice:
  - **Tone** (`neutral | info | success | warning | danger`), which is always spelled
    `variant()`. `Empty` offers two of them and `MenuItem` two, and both keep
    `variant("danger")` so that one name means the same thing everywhere it appears.
  - **Size** (`xs | sm | md | lg`), which is a scale. One that happens to be two steps
    long today (`BadgeSize`) still reads as a step rather than a flag.
- `category: ClassVar[str | None]` sets the docs sidebar group (e.g. `"Actions"`,
  `"Feedback"`). Set it to `None` for composition-only parts (e.g. `TableRow`) that are
  exported but should not get their own docs page.
- **Write the chain, not the shortcut.** A named control takes its name either way, but
  every docstring, `example()` and showcase spells it `TextInput().name("email")` rather
  than `TextInput("email")` — one positional string is the only thing in the API whose
  meaning you have to already know, and it happens to set the submitted name, the `id`,
  the `for` on the label, and the ids the hint and error hang off. The constructor form
  stays supported; it just isn't what we teach.
- **Write markup with hue's own `html`, not htmy's.** Code built on hue (the examples, the
  docs site, and anything a user writes) imports `from hue import html`, whose elements
  chain like components do: `html.a("Docs").href("/docs")`. No public API should need an
  htmy import either: where a component takes an element, it takes a name, as in
  `Text().tag("h1")`. Components still use `htmy.html` inside their own `_render`.
- Named form controls (inputs, checkbox) subclass `FormControl` (`hue-python/src/hue/ui/form.py`),
  which owns `name`/`label`/`disabled`/`required`/`help_text`/`error_text`, `x_model`, `form`, and
  the `aria-describedby` / `aria-errormessage` wiring — don't re-implement those per control.
- Boolean HTML attributes are true by presence: emit `value or None`, never a raw `False`
  (htmy renders `False` as `attr="false"`, which the browser reads as true).
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
- `render_when(condition, component, fallback=UNDEFINED)` — the flag half of the same
  thing, taking the component rather than a factory: there is no value to hand along, so
  a callback would only be a lambda of no arguments everywhere. Use it for a bool
  (`dismissible`, `required`) and for an optional collection, whose emptiness is a
  condition rather than a value. Writing `render_if(flag or None, lambda _: …)` is the
  smell this replaces: `render_if` tests against `None`, so a `False` would render.

AJAX swaps have their helpers in `hue-python/src/hue/ui/navigation.py`: `swap(target)` for
a link or form that swaps a region and pushes its URL, `SYNC` for an element that
refreshes itself from any response that carries it, and the `SwapsTarget` mixin for a
component whose links swap a region it sits outside of.

### Design tokens (`hue-python/src/hue/static/styles/tailwind.input.css`)

Two layers. The `--hue-*` ramps are the raw palette. They are plain custom properties, not
`@theme` entries, so they generate **no utilities** — there is no `bg-gray-500` to reach for,
and a component that wants a colour has to name a semantic alias. A class list should read in
those terms:

| Use | Classes |
| --- | --- |
| Surfaces | `bg-canvas`, `bg-canvas-subtle`, `bg-surface`, `bg-surface-raised`, `bg-surface-hover`, `bg-surface-active`, `bg-surface-sunken`, `bg-scrim` |
| Text | `text-fg`, `text-fg-strong`, `text-fg-muted`, `text-fg-subtle`, `text-fg-disabled` |
| Borders | `border-border`, `border-border-strong`, `border-border-input`, `border-border-hover` |
| Accent | `bg-accent`, `hover:bg-accent-hover`, `text-accent-fg`, `bg-accent-subtle`, `border-accent-border`, `text-accent-text` |
| Status | `success`, `warning`, `danger`, `info`, each with `-fg` `-subtle` `-border` `-vivid` |
| Charts | `chart-1` to `chart-6`, for categories a chart tells apart (chart-1 is the accent, chart-6 the muted grey) |
| Shape | `rounded-md` controls, `rounded-lg` containers, `rounded-xl` overlays, `rounded-full` avatars/switches |
| Height | `h-control-xs\|sm\|md\|lg` (28/32/36/44px, bumped on coarse pointers) |
| Elevation | `shadow-field`, `shadow-ring`, `shadow-raised`, `shadow-overlay` |

Because the aliases flip in the `[data-theme="dark"]` block, a correctly-tokened component
needs **no `dark:` variants** — reach for one only where dark genuinely differs in structure.
`text-base` is 14px (the UI default, not 16) and the body weight is 500, not 400.
`--color-accent-vivid` is decorative only in light mode; it fails contrast on white.

A `LEGACY` block at the bottom of that file holds the pre-design-system names
(`primary`, `surface-*`, `secondary-*`, `background`, and the handful of
`wg-*` ramp names Callout still uses) at their original values, so unmigrated components keep
working. **Never reference those from new code** — the block shrinks as components migrate
and is deleted with the last of them.

To restyle Hue, redefine a `--hue-*` ramp step and everything built on it moves with it, in
both themes; to change one role only, redefine that alias.

## Docs auto-discovery (don't break it)

This section is about v1 (`hue-docs/src/hue_docs/`). Docs v2 (`src/hue_docs_v2/`)
declares its pages in Python and does not read `example()`; its rules are in
`hue-docs/CLAUDE.md`. v1 stays until v2 replaces it, so keep `example()` working for now.

`hue-docs` introspects `hue.ui.__all__`, keeps `ChainableComponent` subclasses, derives
"axes" from `Literal` enum and `bool` modifier signatures, and reads default values out of
the `_render` source via the AST (`_get_prop("name", <literal>)`). Practical rules so a new
component shows up correctly:

- Every documented component **must** define `example()` — the docs build fails loudly
  otherwise — and its body must be a **single `return` expression** (its source is shown
  verbatim as the usage snippet; a test enforces this).
- Use real `Literal` type aliases for variant axes (so they resolve as enum axes).
- Defaults are read from the **literal** second argument of `_get_prop("name", <literal>)`
  in `_render` (via the AST), then overlaid with anything the constructor pre-sets in
  `_props`.
- **Every `Literal`/`bool` modifier becomes a control**, so each one has to change what
  `example()` renders — a test in `hue-docs` fails when an axis comes out identical for every
  value, because a knob that does nothing reads as a broken page. Either give the modifier a
  visible effect, or take the `Literal`/`bool` out of its signature: a semantic-only knob
  belongs as a keyword-only argument on the modifier it qualifies
  (`Empty.title(value, *, heading=None)`), which also keeps it off the playground.
- `hue-docs` pins `htmy==0.8.2` (APIs removed in 0.9+); keep core compatible with that pin.

## Testing

Tests live in each package's `tests/`. In `hue-python`, there is **one test file per
component** under `tests/components/`, shared fixtures in `tests/conftest.py`, and shared
accessibility helpers in `tests/_a11y.py`.

There are two tiers, and almost all of CI's time goes to the second:

- **Markup** (`tests/components/`, `tests/test_*.py`): render with the `context_args`
  fixture and `await render_tree(component, context_args=context_args)` (mark the test
  `@pytest.mark.asyncio`), then assert through the `tests/_a11y.py` parse helpers rather
  than substring checks.
- **Browser** (`tests/browser/`): the component in a page in the installed Chrome, driven
  with real keys and pointer moves through Playwright's sync API. The `show` fixture takes
  components (and `width`, `theme`, `dir`), returns the page once Alpine has started, and
  fails the test on any console error. It runs with the rest of `uv run pytest tests`.

**Every test answers one question: what realistic bug makes it fail, and would anything
else catch it first?** Types and the hue-docs suite already catch a lot: it renders every
page and frame, and fails on an id used twice, a class missing from the stylesheet, a
console error, or a page wider than the window at desktop and phone width. A test with no realistic bug
behind it, or one something else catches first, does not get written. Skip edge cases
nobody hits.

### Accessibility (WCAG 2.2 AA)

Every component is covered here, where the rest of the suite samples. Each requirement goes
in the tier that can see it.

- **Markup, every component:** the semantic element and `role`; an accessible name on
  every interactive element (a required one raises when missing); labels, hints and errors
  wired to their control (`for`, `aria-describedby`, `aria-errormessage`,
  `aria-invalid`); state exposed (`aria-expanded`, `aria-selected`, `aria-checked`,
  `aria-current`, `aria-busy`, `disabled`); a live region where content changes without a
  page load; `sr-only` rather than `invisible` or `display: none` for text that is only
  visually hidden.
- **Browser, every interactive component:** the keyboard pattern from the WAI-ARIA
  Authoring Practices for that widget; focus that is visible and lands where it should
  (into an overlay on open, back to the trigger on close, never on `<body>`); a modal that
  traps focus; Escape closing only the innermost overlay; no horizontal scroll at 320px
  wide; 24px targets on a coarse pointer; reduced motion honoured; RTL wherever direction
  changes the behaviour.
- **Once, for every component**, in hue-docs' `test_pages.py` over every page and frame:
  no id twice, no boolean attribute written `"false"`, every `svg` either `aria-hidden` or
  named. A rule that holds everywhere goes there, not into each component's file.

### Markup tier

Cover:

1. The form contract: the name and value a control submits, `type="button"` against
   `type="submit"`, and disabled meaning inert to the keyboard and the form.
2. Escaping of text inside Alpine expressions and inline scripts.
3. Real logic (the router, `Formats`, `TableState`, pagination, chart data, date ranges),
   tested like a pure function with one parametrized table of representative cases. Logic
   that is hard to reach through `_render` wants pulling out into a function.
4. Each error the API promises to raise, once, with one or two bad inputs.
5. A bug that shipped, once, with the test named after the behaviour.

### Browser tier

1. Behaviour only: keyboard, focus, pointer, overlays, layout geometry, Alpine state.
   Anything a markup test can see goes in the markup tier.
2. One file per component, named after it, and no file for a fix round or a review.
3. A matrix covers the edges, not the grid: the narrowest width and one wide one, coarse
   pointer only where it changes a size, RTL only where it changes a direction. A parameter
   that never changes the outcome comes out.
4. A fix to keyboard, focus, pointer, overlay or layout behaviour lands with a test that
   failed before it, in the component's file, extending an existing test where one is
   close. The fix is done when the whole suite passes, not only its own test.
5. Wait on a condition, never a fixed delay. A test that takes more than about two seconds
   needs a reason.

### Don't test

- Tailwind classes as a stand-in for appearance. A class is fine where it is the behaviour
  (`sr-only`, `hidden`, `opacity-0` against `invisible`).
- A styling default, or the off branch of a conditional unless the absence is the contract
  (no `aria-invalid` on a valid field, no `aria-describedby` pointing at nothing).
- A modifier that writes its value straight through to an attribute, the shared
  `ChainableComponent` modifiers (tested once in `tests/test_base.py`), and anything a type
  or the hue-docs suite already enforces.

## Component quality bar

Every component must satisfy these — review against them before finishing:

- **Accessibility first (hard requirement).** Prefer semantic HTML over `div` soup; wire up
  the ARIA helpers already on the base; ensure keyboard operability and visible focus
  (`focus-visible:outline…`, see `Button`); associate labels with inputs; use live regions /
  `aria-hidden` appropriately. When unsure, pick the most accessible established pattern
  (cross-check WAI-ARIA Authoring Practices) and say so.
- **Get the API right, don't preserve mistakes.** Hue is pre-1.0 with no external
  consumers, so renaming a modifier, dropping a variant, or changing a default is fine when
  the new shape is clearly better — just do it in one place, update every call site and
  test, and say so in the PR. No deprecation aliases: two names for one thing is exactly the
  confusion a consumer framework can't afford.
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
  to code in plain words (`size-4`, `aria-hidden`, `create_icon_base`). Always start a
  docstring on a new line after the opening `"""` (summary on the second line), including
  one-line docstrings.
- **Component docstrings stay short.** A one-line summary of what it is, then a sentence or
  two on the modifiers. Around eight lines is plenty. At most one short example, and only
  where the shape isn't obvious from the summary — the docs page already renders `example()`
  verbatim as the usage snippet.
- **Design intent goes in the defaults, not the prose.** The design guide leads internal
  development — it describes what is *intended*, not what is enforced. Express that intent by
  choosing the default and the set of variants: Badge starts `neutral`, Card starts flat
  rather than raised, the accent is the step that clears contrast. A consumer gets the
  intention for free and can override all of it. What must not go in is usage rules, taste,
  or predictions about end users ("exactly one primary per viewport", "a table where every
  row is tinted has taught the reader to ignore colour"): an intention shapes what someone
  gets by default, an opinion just sits in the docstring being unactionable. Facts about the
  *code* are fine and often necessary — an icon-only button takes its label as an argument
  because an icon has no accessible name; a skeleton renders `aria-hidden`, so `aria-busy`
  belongs on the region around it.
- Priority order: **correctness → performance → readability/reusability.**

### Mistakes we have already made

A sweep of every component found the same bugs in unrelated places. Check new work
against each of these.

- **Ids are unique on the page and built from the component's own id.** Build them from
  `_input_id()` or an Alpine `$id`, never from a name alone, a slug, or raw user text.
  Same-named checkboxes, radio values with a space, slugged Select options and
  Pagination's `page_size` all collided. The hue-docs suite checks ids on every page; an
  id that depends on a value or an option needs its own test with two of them on one page.
- **Move focus before hiding the element that has it.** `x-show="false"` or `$el.remove()`
  on a focused element drops focus to `<body>`, which Alert, Toast, Command and a Dialog
  that started open all did. Decide where focus goes (the trigger, the next control, the
  container) as part of the change.
- **Overlays handle Escape on their own root and stop it there.** `.window` listeners all
  fire at once, so one Escape closed a popover and the dialog around it, and cleared a
  table's selection. Use `.window` only for something that must close while focus is
  elsewhere, such as Tooltip.
- **No text inside an expression or an inline script.** Render it as markup, or quote it
  with `json.dumps`; inside a `<script>`, also escape `<`, `>` and `&`. A slider suffix of
  " o'clock" broke its readout, and a `</script>` in the CSRF token could close the page's
  script.
- **Merge attributes through `_control_attrs` (or the base equivalent).** Spreading
  `**self._get_base_html_attrs()` last lets a caller's attribute replace a computed one (a
  RadioGroup's hint vanished from `aria-describedby`), and spreading it beside an explicit
  `id=` raises a TypeError.
- **hue's own wiring never shares an attribute key with a public modifier.** Internal
  listeners and bindings use `x-on:…` and `x-bind:…`, the public modifiers write `@…`
  and `:…`, so both survive. The overlay's `@click` used to replace the trigger's
  `on_click`.
- **Name Alpine state so a nested scope cannot shadow it.** A Tooltip's `open` hid the
  DropdownMenu's `open` around it. `x-ref` registers on the nearest `x-data`, so it does
  not cross a component boundary safely either.
- **Disabled means inert to the keyboard and the form.** `aria-disabled` with
  `pointer-events-none` still lets Enter activate the element, and a hidden input still
  submits. Drop the handlers and disable the inputs.
- **Test `""`, `0` and `None` separately.** `if value` treated an "All" option valued `""`
  as no value at all.
- **A required accessible name raises when it is missing,** as ScrollArea does. Any rule a
  docstring states gets the same treatment: enforce it in code or drop it.
- **Clamp or drop input from a URL or a form where it enters:** a page past the last, a
  non-number in a numeric filter, NaN, a body that is not UTF-8.
- **Check behaviour in a browser.** The tests read markup, and every keyboard and focus bug
  above passed them. Anything with keyboard, focus or overlay behaviour gets a test in
  `tests/browser/` with real keys and pointer moves.

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
  Django path params (`<name>` and `<converter:name>`), injects the CSRF token into
  `HueContextArgs`, and wraps sync handlers in `sync_to_async`. AJAX detection
  (`X-Requested-With` / `X-Alpine-Request`) lives in the core router.
- `.urls` is built once per class and never mutates the user's `router` (the index is
  registered on a private router via `Router.page`), so subclasses get their own index.
- Body validation failures return 422 via the overridable
  `handle_body_validation_error(request, exc)` hook.
- `HueAssetsMiddleware` (`middleware.py`) — serves `/__hue__/styles.css`,
  `/__hue__/js/alpine.js` and, beside it, `/__hue__/js/chart-bundle.js` straight from
  the `hue` package (no `collectstatic`), sync and async capable, with RFC 7232
  conditional (ETag / 304) handling. The Alpine bundle sends the CSRF token as `X-CSRFToken`,
  the header Django reads.
- Tests configure Django in `conftest.py` and use the `urlpatterns_` fixture for isolation.

## FastAPI integration (`hue-fastapi/src/hue_fastapi/`)

The same surface as hue-django. Where the two differ:

- `configure_hue(app, csrf=...)` stores a `HueConfig` on `app.state` and adds the
  `/__hue__/` asset routes. `csrf` is required; `None` turns hue's checks off.
- `HueView` / `HueFragmentsView` expose `.api_router` for `app.include_router`. Each route
  becomes a FastAPI endpoint whose signature is the handler's parameters after
  (view, request, context), less `body`, so path params, query params and `Depends`
  resolve as usual.
- hue's request hooks are synchronous and Starlette's body is a coroutine, so the endpoint
  reads the body of every unsafe request before dispatch and leaves it on `request.state`
  (`preload_body`). Every unsafe request, not only ones with a `body` parameter: a table's
  actions read the posted ids through `_get_form_values`.
- `_url_for` works out the mount prefix from the request path (`Mount.of`), not from route
  names, so a view mounted twice links into the mount the reader is in.
- CSRF is a signed double-submit cookie (`csrf.py`), read from the `X-CSRFToken` header
  the Alpine bundle sends or the `csrf_token` field. Both names are fixed, since hue
  depends on them. With `cookie_secure` the cookie takes the `__Host-` prefix, so a
  sibling subdomain cannot plant one.
- `HueRequestMiddleware` carries toasts across a redirect and needs Starlette's
  `SessionMiddleware` outside it. The session load and save live in `hue.toast`
  (`restore_from_session`, `keep_in_session`), shared with hue-django.
- The asset table, cache and Cache-Control rule live in `hue.assets` (`ASSET_ROUTES`,
  `served_asset`, `versioned_url`, `cache_control`), shared with hue-django. Tests stub
  an asset with `monkeypatch.setitem(assets.ASSET_ROUTES, ...)` and reset
  `assets._served`.
- A route hue registers for a view (a table's action) spells its parameter through
  `Router._path_param`, so core never writes one framework's path syntax.

## House rules

- Run `make lint` (or `/check`) before finishing.
- No relative imports across parent packages (`ban-relative-imports = "parents"`).
- Start component files with `from __future__ import annotations`.
