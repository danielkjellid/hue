# hue-docs

The documentation site for [hue](../hue-python), written with hue itself. A FastAPI
app renders every page; the build freezes them into static files, and Cloudflare
serves those with a small Python Worker for the live demos.

```bash
make serve-v2     # live on http://localhost:8001
make build-v2     # freeze the site into dist-v2/
make preview-v2   # the frozen site and the Worker together, as Cloudflare runs them
make test
```

`.github/workflows/docs-deploy.yml` deploys `main` to production and uploads a
preview for every other branch. How to write a page is in [CLAUDE.md](CLAUDE.md).
