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
- **Cloudflare Workers** — this is what gives a preview URL per pull request.
  `.github/workflows/docs-deploy.yml` builds the site and ships it: production
  for `main`, a preview version aliased to the branch for everything else, so
  `ds/button` lands at `ds-button-<worker>.<subdomain>.workers.dev`.
  `wrangler.jsonc` here declares it as a static-asset Worker - no code, just
  `dist/`.

  It builds on **every branch**, so any push gets a preview, and the build runs
  in CI rather than in Workers Builds. That image ships no Python and installs
  one with asdf, which compiles it from source: **228 seconds**, against 3 for
  the dependencies it then installs. It also reports "No dependencies detected
  to cache" for a uv project, so there is nothing to warm up either. The
  workflow instead uses the same setup action as the rest of CI, which restores
  a virtualenv the lint and test jobs have usually already cached. The Tailwind
  CLI is cached separately, because pytailwindcss drops an 80MB binary into
  site-packages the first time it runs and those jobs never invoke it.

  Deploying needs `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` as
  repository secrets, and the Workers Builds Git integration turned off so the
  two do not both build.

Internal URLs are root-relative (`/styles/...`, `/js/...`) by default, which is
correct for a domain root. When the site is served from a **subpath** (e.g. a
GitHub Pages project site at `…/<repo>/`), set `HUE_DOCS_BASE_URL=/<repo>` at
build time and every emitted URL is prefixed accordingly — the `dist/` file
layout stays flat regardless.
