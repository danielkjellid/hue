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

- **Fully auto-discovered** — every `ChainableComponent` exported from `hue.ui`
  is found automatically and gets a page; new components appear in the sidebar
  with **no per-component files to write**. Each page is derived from the
  component itself:
  - the preview content comes from the component's `example()` classmethod
    (defined on the component in `hue-python`),
  - the variant grids come from its introspected `Literal` axes,
  - the usage snippet comes from the source of `example()`, and
  - the docstring becomes the page intro.
- **Interactive playground** — a live preview plus a props table whose
  selects/checkboxes drive it, built from the introspected enum/bool axes. The
  site is static, so every combination is pre-rendered and Alpine `x-show`s the
  selected one (capped per component — see `layout/playground.py`).
- **Sidebar subsections** — components are clustered into categories (Layout,
  Typography, Actions, Inputs, …) defined in `src/hue_docs/categories.py`.
- **Syntax highlighting** — code blocks are highlighted at build time with
  Pygments (no client-side highlighter), themed for light and dark.
- **Prose in Python** — the intro/install/usage/framework pages live in
  `src/hue_docs/content/`, written with hue's own components.

To document a new component, give it an `example()` classmethod in `hue-python`
returning a representative instance in a single expression; that is the one hook
the docs read, and the build fails loudly if it is missing. Composition-only
parts (such as `TableRow`) opt out with `category = None`.

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
  publishes `dist/` on push to `main`. It works for project sites too: the
  workflow reads the serving subpath from `configure-pages` and passes it as
  `HUE_DOCS_BASE_URL` so links/assets resolve correctly.
- **Cloudflare Workers** — this is what gives a preview URL per pull request,
  which is the reason to run one alongside Pages. `wrangler.jsonc` here declares
  the site as a static-asset Worker (no code, just `dist/`), so connecting the
  repo in Workers Builds needs only:

  | Setting | Value |
  | --- | --- |
  | Build command | `curl -LsSf https://astral.sh/uv/install.sh \| sh && export PATH="$HOME/.local/bin:$PATH" && make build` |
  | Deploy command | `npx wrangler deploy` |
  | Non-production branch deploy command | `npx wrangler versions upload` |
  | Path | `hue-docs` |

  Two things that are easy to get wrong. `Path` is `hue-docs`, the directory
  holding `wrangler.jsonc`, and **not** `hue-docs/dist` — build and deploy both
  run from it, which is also why the build command does not `cd` anywhere. And
  the whole repository is still cloned, which matters because hue-docs installs
  `hue` from `../hue-python` as an editable path dependency.

  The build image ships no `uv`, hence installing it first; `uv` then fetches
  Python 3.13 itself, so the image's own Python version does not matter, and
  `make build` pins the Tailwind CLI. Leave `HUE_DOCS_BASE_URL` unset — every
  deployment is served from its own root.

  `versions upload` publishes a version without promoting it to production, so
  a pull request gets a preview URL while `main` keeps serving the live site.

  A **Cloudflare Pages** project reaches the same place with no file in the
  repo (build command as above but with `cd hue-docs &&`, output directory
  `hue-docs/dist`, root directory left at the repository root). Cloudflare now
  steers new projects to Workers, so that is what this is set up for.

Internal URLs are root-relative (`/styles/...`, `/js/...`) by default, which is
correct for a domain root. When the site is served from a **subpath** (e.g. a
GitHub Pages project site at `…/<repo>/`), set `HUE_DOCS_BASE_URL=/<repo>` at
build time and every emitted URL is prefixed accordingly — the `dist/` file
layout stays flat regardless.
