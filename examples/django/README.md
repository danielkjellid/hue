# Django example

A small Django app built on hue: one page with a declared invoices table on it,
backed by SQLite. It exists to try components against a real database and a
real browser, which the packages' own tests cannot.

```bash
make serve   # builds hue's stylesheet, migrates, seeds, serves on :8001
make test    # the database tests
make lint
```

`make serve` reseeds every time, with the same 64 invoices, so anything you
archive or mark as paid comes back on the next run.

It is its own uv project, like `hue-docs`. `hue` and `hue-django` are installed
from the working tree as editable path dependencies, so a change in either shows
up here on the next request.

The table lives in `example/invoices/views.py`. The page is mounted under
`/billing/` instead of the site root, so the table's URLs have to follow the
mount point.
