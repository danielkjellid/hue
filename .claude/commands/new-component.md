---
description: Scaffold a new Hue atom or molecule (component + export + tests)
argument-hint: <Name> <atom|molecule> [category] — optionally paste a React reference after
---

Scaffold a new component end to end. Arguments: `$ARGUMENTS` (component name, then
`atom` or `molecule`, then an optional docs sidebar category; the user may also paste a React
component below as the visual/behavioral reference).

Read `@CLAUDE.md` first — the "chainable-component pattern", "Component quality bar",
"Testing", and "Docs auto-discovery" sections are the spec for this command.

## Steps

1. **Study the templates.** Read `hue-python/src/hue/ui/base.py` and a close sibling
   (`hue-python/src/hue/ui/atoms/button.py` for an atom,
   `hue-python/src/hue/ui/molecules/callout.py` for a molecule) so the new file matches the
   established idiom exactly. Reuse base modifiers and `hue/utils.py` helpers — don't
   reinvent them.

2. **Create the component** at `hue-python/src/hue/ui/{atoms,molecules}/<name>.py` with:
   `from __future__ import annotations`; `Literal` type aliases for variant/size axes;
   the class with `category`, an `example()` classmethod (single simple expression),
   chainable modifier methods returning `Self`, and `_render` reading props via
   `_get_prop` and splatting `_get_base_html_attrs()`.

3. **Export it** in `hue-python/src/hue/ui/__init__.py` — add the import and the
   alphabetized `__all__` entry.

4. **Add a focused test** at `hue-python/tests/components/test_<name>.py` using the
   `context_args` fixture and the `tests/_a11y.py` helpers. Cover: each variant renders as
   expected, key props change output, accessibility invariants, and **every conditional in
   `_render` tested both ways** (present and absent). Do not over-test; don't re-test base
   modifiers.

5. **Verify**: from `hue-python/`, run `make lint` and `uv run pytest tests`. Optionally
   rebuild docs (`cd hue-docs && PYTHONPATH=src uv run python -m hue_docs`) to confirm the
   component is auto-discovered.

## Quality checklist (self-review before finishing)

- Accessibility: semantic element, ARIA wired via base helpers, keyboard + visible focus,
  labels associated, decorative icons `aria-hidden`.
- Backwards compatible, declarative/simple API, DRY (new util ⇒ used in ≥2 places),
  no over-complicated Tailwind, comments explain *why* not *what*.

## If a React reference was provided

Mimic its look and API intent, but re-express it in the chainable `htmy` idiom (not a 1:1
port) and **upgrade its accessibility** to meet the bar. Map its props to modifier methods
and its variants to `Literal` axes.
