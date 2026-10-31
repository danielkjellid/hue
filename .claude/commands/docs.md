---
description: Rebuild and serve the hue-docs site
---

Build and serve the documentation site.

1. From `hue-docs/`, run `make serve` in the background. It builds the stylesheet,
   scripts and search index, then serves the pages live on http://localhost:8001.
   Report any build error.
2. To confirm a page renders, fetch it, e.g.
   `curl -s -m 4 http://localhost:8001/components/<slug>/ -o /dev/null -w "HTTP %{http_code}\n"`,
   and report the status.

New Tailwind classes need another run, since nothing watches the CSS.
