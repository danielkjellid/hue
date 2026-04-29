## FastAPI Integration Notes

This document outlines how to implement the same built-in asset serving pattern for FastAPI/Starlette.

### Approach

The same `hue.assets` module from the core package provides asset discovery. A Starlette middleware intercepts `/__hue__/` requests and serves the assets.

### Middleware

```python
# hue_fastapi/middleware.py

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from hue.assets import read_css, read_js

HUE_ASSETS_PREFIX = "/__hue__/"

_ASSET_ROUTES = {
    "styles.css": (read_css, "text/css; charset=utf-8"),
    "js/alpine.js": (read_js, "application/javascript; charset=utf-8"),
}

_cache: dict[str, tuple[str, str]] = {}


def _get_cached_asset(path: str) -> tuple[str, str]:
    if path not in _cache:
        import hashlib
        reader, _ = _ASSET_ROUTES[path]
        content = reader()
        etag = hashlib.md5(content.encode()).hexdigest()
        _cache[path] = (content, etag)
    return _cache[path]


class HueAssetsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith(HUE_ASSETS_PREFIX):
            return await call_next(request)

        asset_path = request.url.path[len(HUE_ASSETS_PREFIX):]

        if asset_path not in _ASSET_ROUTES:
            return await call_next(request)

        content, etag = _get_cached_asset(asset_path)
        _, content_type = _ASSET_ROUTES[asset_path]

        if_none_match = request.headers.get("if-none-match", "")
        if if_none_match == etag:
            return Response(status_code=304)

        return Response(
            content=content,
            media_type=content_type,
            headers={"ETag": etag, "Cache-Control": "public, max-age=3600"},
        )
```

### Usage

```python
from fastapi import FastAPI
from hue_fastapi.middleware import HueAssetsMiddleware

app = FastAPI()
app.add_middleware(HueAssetsMiddleware)
```

### Page Configuration

```python
# hue_fastapi/pages.py

from hue.pages import create_page_base
from hue_fastapi.middleware import HUE_ASSETS_PREFIX

Page = create_page_base(
    css_url=f"{HUE_ASSETS_PREFIX}styles.css",
    js_url=f"{HUE_ASSETS_PREFIX}js/alpine.js",
    html_title_factory=lambda title: f"{title} - Hue",
    extra_css_urls=[],  # User configures via their own mechanism
)
```

### Key Differences from Django

- Uses Starlette's `BaseHTTPMiddleware` instead of Django's middleware protocol
- Configuration is passed directly (no Django settings system)
- Users configure `extra_css_urls` via their own approach (environment variables, config file, etc.)
