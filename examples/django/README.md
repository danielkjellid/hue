# Django example

A small Django app built on hue: a page with a declared invoices table and a
page with a declared events calendar, both backed by SQLite. It exists to try
components against a real database and a real browser, which the packages' own
tests cannot.

```bash
make serve   # builds hue's stylesheet, migrates, seeds, serves on :8001
make test    # the database tests
make lint
```

`make serve` reseeds every time, with the same 64 invoices and the same events
placed around the current week, so anything you archive, mark as paid, move or
delete comes back on the next run.

It is its own uv project, like `hue-docs`. `hue` and `hue-django` are installed
from the working tree as editable path dependencies, so a change in either shows
up here on the next request.

The table lives in `example/invoices/views.py` and the calendar in
`example/events/views.py`, with its series expanded in `repeats.py`. The pages
are mounted under `/billing/` and `/events/` instead of the site root, so their
URLs have to follow the mount point.
