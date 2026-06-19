---
description: Scaffold a hue-django HueView or HueFragmentsView with a Router
argument-hint: <ViewName> [full|fragments]
---

Scaffold a Django view for the `hue-django` package. Arguments: `$ARGUMENTS` (view name, then
`full` for a page view or `fragments` for a router-only view; default `full`).

Read the "Django integration" section of `@CLAUDE.md` and the existing implementations first:
`hue-django/src/hue_django/views.py` and `hue-django/src/hue_django/router.py`.

## Steps

1. **Create the view** following the established pattern:
   - `full`: subclass `HueView` with an `index(self, request, context) -> BasePage` (async
     preferred) returning a page built from `hue.ui` components, plus an optional
     `router = Router[HttpRequest]()` for AJAX fragments via `@router.fragment_post(...)`.
   - `fragments`: subclass `HueFragmentsView` with only a `router` and its fragment handlers.
2. Use Django path-param syntax in routes (`<int:id>`); the `Router` injects the CSRF token
   and wraps sync handlers in `sync_to_async`, so handlers may be sync or async.
3. **Add a test** under `hue-django/tests/` mirroring `test_views_hue_view.py` /
   `test_views_hue_fragments.py` — use the `urlpatterns_` fixture and assert on rendered
   responses (index renders, fragment routes respond, AJAX detection works).
4. **Verify**: from `hue-django/`, run `make lint` and `uv run pytest tests`.
