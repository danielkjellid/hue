# hue-docs

The documentation site for [hue](../hue-python). It is a small **static site
generator** that dogfoods hue itself: it introspects the component library,
renders a showcase for every component, and writes a plain `dist/` folder of
HTML/CSS/JS that can be deployed anywhere.

## How it works

```
discover components  ->  render pages (hue's own render_tree + BasePage)  ->  dist/
        |                                                                     |
   hue.ui.__all__                                                      tailwindcss CLI
   introspect Literal/bool modifiers                                   builds dist/styles/tailwind.css
```

- **Auto-discovery** — every `ChainableComponent` exported from `hue.ui` is
  found automatically and gets a page. New components appear in the sidebar
  without editing any navigation. Their `Literal`/`bool` modifiers (e.g.
  `variant`, `size`, `shape`) are introspected into a variant grid.
- **Interactive playground** — components with a `PlaygroundSpec` get a live
  preview plus a props table whose selects/checkboxes drive it. The site is
  static, so every combination is pre-rendered and Alpine `x-show`s the
  selected one (capped per component — see `layout/playground.py`).
- **Optional rich examples** — drop a module in `src/hue_docs/examples/` to
  hand-author nicer showcases (and a playground) for a component. Without one,
  the auto grid is used as a fallback.
- **Sidebar subsections** — components are clustered into categories (Layout,
  Typography, Actions, Inputs, …) defined in `src/hue_docs/categories.py`.
- **Syntax highlighting** — code blocks are highlighted at build time with
  Pygments (no client-side highlighter), themed for light and dark.
- **Prose in Python** — the intro/install/usage/framework pages live in
  `src/hue_docs/content/`, written with hue's own components.

The site is static, so live Alpine-AJAX demos can't hit a backend — those are
shown as code. Everything client-side (theme toggle, inputs, nav) works through
the Alpine bundle that hue already ships.

## Develop

```sh
make build      # render the site into dist/
make serve      # serve dist/ at http://localhost:8000
make watch-css  # rebuild CSS on change (run alongside `make build`)
make lint       # ruff + mypy + deptry
make test       # pytest
```

`make build` runs `python -m hue_docs`, which renders the pages **and** runs the
Tailwind CLI to produce `dist/styles/tailwind.css`.

## Deploy

`dist/` is plain static output. Deploy it with any static host:

- **GitHub Pages** — the `.github/workflows/docs.yml` workflow builds and
  publishes `dist/` on push to `main`.
- **Vercel / Cloudflare Pages / Netlify** — set the build command to
  `cd hue-docs && uv run python -m hue_docs` (or `make -C hue-docs build`) and
  the output directory to `hue-docs/dist`.

Assets are referenced with root-relative URLs (`/styles/...`, `/js/...`), so the
site expects to be served from a domain root (the default on Vercel/Pages with a
custom domain).
