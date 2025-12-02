# Views and Router

This document covers Django-specific usage of Hue views and router. For general information about the router architecture and concepts, see the [core router documentation](../../hue-python/docs/router.md).

## Overview

Hue Django provides two main view classes for building AJAX-first applications:

1. **`HueView`**: Full page views with optional AJAX fragment routes
2. **`HueFragmentsView`**: Fragment-only views for API-like endpoints

Both views use the Django-specific `Router[HttpRequest]` to define routes that return HTML fragments.

## Router

The Django router (`hue_django.router.Router`) extends the base `Router` class and handles Django-specific details:

- **Django URL pattern syntax**: Uses Django's `<type:name>` parameter syntax
- **CSRF token extraction**: Automatically extracts CSRF tokens from Django requests
- **AJAX detection**: Checks Django's `request.META` for AJAX headers

### Creating a Router

```python
from hue_django.router import Router
from django.http import HttpRequest

class MyView(HueView):
    router = Router[HttpRequest]()
```

The router is automatically instantiated if not provided in `HueView` (but required for `HueFragmentsView`).

### Path Parameter Syntax

Django routers use Django's URL pattern syntax for path parameters:

```python
@router.fragment_get("comments/<int:comment_id>/")
async def get_comment(
    self,
    request: HttpRequest,
    context: HueContext[HttpRequest],
    comment_id: int,  # Extracted from path
):
    return html.div(f"Comment {comment_id}")
```

Supported parameter types include:

- `<int:name>` - Integer parameter
- `<str:name>` - String parameter
- `<slug:name>` - Slug parameter
- `<uuid:name>` - UUID parameter
- `<path:name>` - Path parameter (matches including slashes)

For more details on Django path converters, see the [Django URL documentation](https://docs.djangoproject.com/en/stable/topics/http/urls/#path-converters).

### Multiple Path Parameters

You can define multiple path parameters in a single route:

```python
@router.fragment_get("users/<int:user_id>/posts/<int:post_id>/")
async def get_post(
    self,
    request: HttpRequest,
    context: HueContext[HttpRequest],
    user_id: int,
    post_id: int,
):
    return html.div(f"Post {post_id} by user {user_id}")
```

## HueView

`HueView` is designed for full page views that can also handle AJAX fragment updates. It requires an `index` method that handles the initial page load.

### Basic Usage

```python
from hue_django.views import HueView
from hue_django.pages import Page
from hue_django.router import Router
from django.http import HttpRequest
from hue.context import HueContext
from htmy import html

class LoginView(HueView):
    async def index(
        self, request: HttpRequest, context: HueContext[HttpRequest]
    ):
        return Page(body=html.div("Login Page"))

    router = Router[HttpRequest]()

    @router.fragment_post("login/")
    async def login(
        self, request: HttpRequest, context: HueContext[HttpRequest]
    ):
        # Process login form
        return html.div("Login successful")
```

### Requirements

- **Must define `index` method**: The `index` method handles GET requests to the root path (`/`)
- **`index` must be async**: The method must be defined as `async def index(...)`
- **Returns a `Page`**: The `index` method should return a `Page` instance (full HTML page)
- **Router is optional**: If no router is defined, one is automatically created for the index route

### Index Method Signature

```python
async def index(
    self,
    request: HttpRequest,
    context: HueContext[HttpRequest],
) -> Page:
    return Page(body=html.div("Content"))
```

The `index` method receives:

- `request`: Django's `HttpRequest` object
- `context`: A `HueContext` object with request and CSRF token

### Fragment Routes

You can add fragment routes to `HueView` using the router:

```python
class CommentsView(HueView):
    async def index(
        self, request: HttpRequest, context: HueContext[HttpRequest]
    ):
        return Page(body=html.div("Comments Page"))

    router = Router[HttpRequest]()

    @router.fragment_get("comments/")
    async def list_comments(
        self, request: HttpRequest, context: HueContext[HttpRequest]
    ):
        return html.div("Comments list")

    @router.fragment_post("comments/")
    async def create_comment(
        self, request: HttpRequest, context: HueContext[HttpRequest]
    ):
        return html.div("Comment created")
```

Fragment routes are **AJAX-only** and return HTML fragments (not full pages).

## HueFragmentsView

`HueFragmentsView` is designed for fragment-only views, typically used for API-like endpoints that only return HTML fragments.

### Basic Usage

```python
from hue_django.views import HueFragmentsView
from hue_django.router import Router
from django.http import HttpRequest
from hue.context import HueContext
from htmy import html

class CommentsFragments(HueFragmentsView):
    router = Router[HttpRequest]()

    @router.fragment_get("comments/")
    async def list_comments(
        self, request: HttpRequest, context: HueContext[HttpRequest]
    ):
        return html.div("Comments list")

    @router.fragment_post("comments/")
    async def create_comment(
        self, request: HttpRequest, context: HueContext[HttpRequest]
    ):
        return html.div("Comment created")
```

### Requirements

- **Must define a router**: Unlike `HueView`, `HueFragmentsView` requires an explicit router
- **No index route**: Fragment views don't have an index route - all routes are fragments
- **All routes are AJAX-only**: All routes require AJAX headers

### When to Use

Use `HueFragmentsView` when:

- You only need fragment endpoints (no full page)
- Building API-like endpoints that return HTML fragments
- Creating reusable fragment collections

Use `HueView` when:

- You need a full page on initial load
- You want both full pages and fragments in the same view

## URL Configuration

Both view classes provide a `urls` class attribute that generates Django URL patterns. Use Django's `include()` function to integrate them into your URL configuration.

### Basic Integration

```python
# urls.py
from django.urls import path, include
from myapp.views import MyView, CommentsFragments

urlpatterns = [
    path("myview/", include(MyView.urls)),
    path("api/comments/", include(CommentsFragments.urls)),
]
```

### How It Works

The `urls` attribute returns a tuple `(urlpatterns, app_name)` compatible with Django's `include()` function:

- **`urlpatterns`**: List of `URLPattern` objects for all routes
- **`app_name`**: Namespace for the view (defaults to the class name in lowercase)

### Custom App Name

You can customize the app name by setting the `app_name` class attribute:

```python
class MyView(HueView):
    app_name = "custom_name"

    async def index(
        self, request: HttpRequest, context: HueContext[HttpRequest]
    ):
        return Page(body=html.div("Content"))
```

## Complete Examples

### Example 1: Full Page with Fragments

```python
from hue_django.views import HueView
from hue_django.pages import Page
from hue_django.router import Router
from django.http import HttpRequest
from hue.context import HueContext
from htmy import html

class BlogView(HueView):
    async def index(
        self, request: HttpRequest, context: HueContext[HttpRequest]
    ):
        return Page(
            body=html.div(
                html.h1("Blog"),
                html.div(id="posts", x_data="posts()"),
            )
        )

    router = Router[HttpRequest]()

    @router.fragment_get("posts/")
    async def list_posts(
        self, request: HttpRequest, context: HueContext[HttpRequest]
    ):
        posts = ["Post 1", "Post 2", "Post 3"]
        return html.div(*[html.p(post) for post in posts])

    @router.fragment_get("posts/<int:post_id>/")
    async def get_post(
        self,
        request: HttpRequest,
        context: HueContext[HttpRequest],
        post_id: int,
    ):
        return html.div(f"Post {post_id}")

    @router.fragment_post("posts/")
    async def create_post(
        self, request: HttpRequest, context: HueContext[HttpRequest]
    ):
        # Process form data
        return html.div("Post created")
```

### Example 2: Fragment-Only View

```python
from hue_django.views import HueFragmentsView
from hue_django.router import Router
from django.http import HttpRequest
from hue.context import HueContext
from htmy import html

class CommentsAPI(HueFragmentsView):
    router = Router[HttpRequest]()

    @router.fragment_get("comments/")
    async def list_comments(
        self, request: HttpRequest, context: HueContext[HttpRequest]
    ):
        comments = ["Comment 1", "Comment 2"]
        return html.div(*[html.p(c) for c in comments])

    @router.fragment_get("comments/<int:comment_id>/")
    async def get_comment(
        self,
        request: HttpRequest,
        context: HueContext[HttpRequest],
        comment_id: int,
    ):
        return html.div(f"Comment {comment_id}")

    @router.fragment_post("comments/")
    async def create_comment(
        self, request: HttpRequest, context: HueContext[HttpRequest]
    ):
        return html.div("Comment created")

    @router.fragment_put("comments/<int:comment_id>/")
    async def update_comment(
        self,
        request: HttpRequest,
        context: HueContext[HttpRequest],
        comment_id: int,
    ):
        return html.div(f"Updated comment {comment_id}")

    @router.fragment_delete("comments/<int:comment_id>/")
    async def delete_comment(
        self,
        request: HttpRequest,
        context: HueContext[HttpRequest],
        comment_id: int,
    ):
        return html.div(f"Deleted comment {comment_id}")
```

## AJAX Requirements

All fragment routes require AJAX headers. The router checks for:

- `X-Requested-With: XMLHttpRequest` header, or
- `X-Alpine-Request: true` header

If a request doesn't have these headers, a `400 Bad Request` response is returned.

### Testing AJAX Requests

When testing with Django's test client, include AJAX headers:

```python
from django.test import Client

client = Client()
response = client.get(
    "/myview/comments/",
    HTTP_X_REQUESTED_WITH="XMLHttpRequest"
)
```

Or use the Alpine header:

```python
response = client.get(
    "/myview/comments/",
    HTTP_X_ALPINE_REQUEST="true"
)
```

## HTTP Methods

All standard HTTP methods are supported for fragment routes:

- `@router.fragment_get(path)` - GET requests
- `@router.fragment_post(path)` - POST requests
- `@router.fragment_put(path)` - PUT requests
- `@router.fragment_patch(path)` - PATCH requests
- `@router.fragment_delete(path)` - DELETE requests

Multiple methods can be defined for the same path:

```python
@router.fragment_get("comments/")
async def list_comments(...):
    return html.div("List")

@router.fragment_post("comments/")
async def create_comment(...):
    return html.div("Create")
```

If a request uses the wrong HTTP method, a `405 Method Not Allowed` response is returned.

## Error Handling

The router automatically handles:

- **Missing AJAX headers**: Returns `400 Bad Request`
- **Wrong HTTP method**: Returns `405 Method Not Allowed`
- **Missing route**: Returns `404 Not Found` (handled by Django)

For custom error handling, you can catch exceptions in your view functions or use Django middleware.

## Best Practices

1. **Use `HueView` for pages**: If you need a full page on initial load, use `HueView`
2. **Use `HueFragmentsView` for APIs**: If you only need fragment endpoints, use `HueFragmentsView`
3. **Return Components**: Always return `Component` instances from view functions, not raw HTML strings
4. **Use path parameters**: Extract dynamic values from the URL using Django's path parameter syntax
5. **Type hints**: Use proper type hints (`HttpRequest`, `HueContext[HttpRequest]`) for better IDE support
6. **Group related routes**: Use separate view classes to group related routes together

## Differences from Core Router

The Django router extends the base router with:

- **Django URL syntax**: Uses `<type:name>` instead of framework-agnostic syntax
- **Django request object**: Works with `HttpRequest` instead of generic request types
- **CSRF token extraction**: Automatically extracts CSRF tokens using Django's `get_token()`
- **AJAX detection**: Checks `request.META` for Django-specific header format

For more information about the core router architecture, see the [core router documentation](../../hue-python/docs/router.md).
