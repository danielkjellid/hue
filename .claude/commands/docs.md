---
description: Rebuild and serve the hue-docs static site
---

Build and serve the documentation site.

1. From `hue-docs/`, build: `PYTHONPATH=src uv run python -m hue_docs` (writes `dist/`).
   Report any discovery/render errors — these usually mean a component broke the
   auto-discovery rules (see "Docs auto-discovery" in `@CLAUDE.md`).
2. Serve it: `make serve` (http.server on http://localhost:8000). Run in the background if
   you need to keep working.
3. To confirm a specific component renders, fetch its page, e.g.
   `curl -s -m 4 http://localhost:8000/<slug>/ -o /dev/null -w "HTTP %{http_code}\n"`,
   and report the status.

For live CSS while editing docs, `make watch-css` (from `hue-docs/`) in a separate process.
