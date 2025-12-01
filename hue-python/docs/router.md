# Router

The Hue Router is a framework-agnostic routing system designed for AJAX-based component updates. It provides a decorator-based API for defining routes that return HTML fragments, which are automatically rendered from Components.

## Overview

The router is designed to work with Hue's AJAX-first architecture. When a user interacts with a page (via Alpine.js AJAX), requests are sent to child routes that return HTML fragments. These fragments are then used to update the DOM without a full page reload.

## Architecture

The router consists of two main components:

1. **`Router[T_Request]`**: The base framework-agnostic router class
2. **Framework-specific routers**: Extend the base router to handle framework-specific details

### Base Router

The base `Router` class provides:

- Route registration via decorators
- View function wrapping (Component → HTML string)
- Path normalization
- AJAX request validation
- Component rendering

### Framework-Specific Routers

Framework-specific routers (like `hue_django.router.Router`) extend the base router and implement:

- `_parse_path_params()`: Parse framework-specific path parameter syntax
- `_get_context_args()`: Extract framework-specific context (request, CSRF token, etc.)

## Basic Usage

The router is used within view classes to define AJAX fragment routes. Framework-specific view classes (like `HueView` in Django) integrate the router to handle route registration and request dispatching.

```python
from hue.router import Router
from hue.context import HueContext
from htmy import html

class MyView:
    router = Router[MyRequest]()

    @router.ajax_get("comments/")
    async def list_comments(
        self, request: MyRequest, context: HueContext[MyRequest]
    ):
        return html.div("Comments list")

    @router.ajax_post("comments/")
    async def create_comment(
        self, request: MyRequest, context: HueContext[MyRequest]
    ):
        return html.div("Comment created")
```

## Route Decorators

The router provides decorators for all standard HTTP methods:

- `@router.ajax_get(path)` - GET requests
- `@router.ajax_post(path)` - POST requests
- `@router.ajax_put(path)` - PUT requests
- `@router.ajax_delete(path)` - DELETE requests
- `@router.ajax_patch(path)` - PATCH requests

All routes are **AJAX-only** - they require either:

- `X-Requested-With: XMLHttpRequest` header, or
- `X-Alpine-Request: true` header

If a request doesn't have these headers, an `AssertionError` is raised.

## Path Parameters

Path parameters are extracted from the route path and passed as keyword arguments to the view function.

### Path Parameter Syntax

Path parameter syntax is framework-specific. Framework-specific routers implement `_parse_path_params()` to handle their syntax.

For example, Django routers use Django's URL pattern syntax:

```python
@router.ajax_get("comments/<int:comment_id>/")
async def get_comment(
    self,
    request: MyRequest,
    context: HueContext[MyRequest],
    comment_id: int,  # Extracted from path
):
    return html.div(f"Comment {comment_id}")
```

The exact syntax depends on the framework-specific router implementation.

### Multiple Parameters

You can define multiple path parameters:

```python
@router.ajax_get("users/<int:user_id>/posts/<int:post_id>/")
async def get_post(
    self,
    request: HttpRequest,
    context: HueContext[HttpRequest],
    user_id: int,
    post_id: int,
):
    return html.div(f"Post {post_id} by user {user_id}")
```

## View Function Signatures

View functions must follow this signature:

```python
async def view_function(
    self,                    # View instance
    request: T_Request,      # Framework request object
    context: HueContext[T_Request],  # Hue context
    **path_params,           # Path parameters as keyword arguments
) -> Component:
    return html.div("Content")
```

### Parameters

1. **`self`**: The view instance (automatically passed)
2. **`request`**: The framework-specific request object (e.g., `HttpRequest` for Django)
3. **`context`**: A `HueContext` object
4. **`**path_params`\*\*: Path parameters extracted from the URL

### Return Type

View functions must return a `Component` (or `Awaitable[Component]` for async functions). The router automatically:

1. Calls the view function
2. Awaits the result if it's a coroutine
3. Renders the Component to an HTML string
4. Returns the HTML string

## Synchronous vs Asynchronous

Both synchronous and asynchronous view functions are supported:

```python
# Async function
@router.ajax_get("async/")
async def async_handler(
    self, request: HttpRequest, context: HueContext[HttpRequest]
):
    return html.div("Async")

# Sync function
@router.ajax_get("sync/")
def sync_handler(
    self, request: HttpRequest, context: HueContext[HttpRequest]
):
    return html.div("Sync")
```

The router automatically handles awaiting coroutines, so you can use either style.

## Complete Example

Here's a complete example showing a view with multiple routes:

```python
from hue.router import Router
from hue.context import HueContext
from htmy import html

class CommentsView:
    router = Router[MyRequest]()

    # List comments (fragment)
    @router.ajax_get("comments/")
    async def list_comments(
        self, request: MyRequest, context: HueContext[MyRequest]
    ):
        comments = ["Comment 1", "Comment 2", "Comment 3"]
        return html.div(
            *[html.p(comment) for comment in comments]
        )

    # Get single comment (fragment with path parameter)
    @router.ajax_get("comments/<int:comment_id>/")
    async def get_comment(
        self,
        request: MyRequest,
        context: HueContext[MyRequest],
        comment_id: int,
    ):
        return html.div(f"Comment {comment_id}")

    # Create comment (fragment)
    @router.ajax_post("comments/")
    async def create_comment(
        self, request: MyRequest, context: HueContext[MyRequest]
    ):
        # Process form data from request
        comment_text = get_comment_from_request(request)
        return html.div(f"Created: {comment_text}")

    # Update comment (fragment)
    @router.ajax_put("comments/<int:comment_id>/")
    async def update_comment(
        self,
        request: MyRequest,
        context: HueContext[MyRequest],
        comment_id: int,
    ):
        return html.div(f"Updated comment {comment_id}")

    # Delete comment (fragment)
    @router.ajax_delete("comments/<int:comment_id>/")
    async def delete_comment(
        self,
        request: MyRequest,
        context: HueContext[MyRequest],
        comment_id: int,
    ):
        return html.div(f"Deleted comment {comment_id}")
```

## Framework-Specific Implementation

To create a router for a new framework, extend the base `Router` class:

```python
from hue.router import Router, PathParseResult
from hue.context import HueContextArgs

class MyFrameworkRouter(Router[MyRequest]):
    def _parse_path_params(self, path: str) -> PathParseResult:
        """Parse framework-specific path parameter syntax."""
        # Extract parameters from path
        # Return PathParseResult(path="final_path", param_names=["param1", "param2"])
        pass

    def _get_context_args(self, request: MyRequest) -> HueContextArgs[MyRequest]:
        """Extract framework-specific context."""
        return HueContextArgs[MyRequest](
            request=request,
            csrf_token=get_csrf_token(request),  # Framework-specific
        )
```

### Required Methods

1. **`_parse_path_params(path: str) -> PathParseResult`**

   - Parse the path to extract parameter names
   - Return a `PathParseResult` with the final path pattern and parameter names
   - The path pattern should be in your framework's URL pattern format

2. **`_get_context_args(request: T_Request) -> HueContextArgs[T_Request]`**
   - Extract the request object and CSRF token
   - Return a `HueContextArgs` TypedDict

## How It Works

1. **Route Registration**: When you use a decorator like `@router.ajax_get("path/")`, the router:

   - Normalizes the path
   - Parses path parameters
   - Wraps the view function
   - Stores the route

2. **Request Handling**: When a request comes in:

   - The framework-specific view (e.g., `HueView`) finds the matching route
   - Calls the wrapped view function with the request and path parameters
   - The wrapped function validates AJAX headers
   - Creates a `HueContext` and calls the original view function
   - Renders the returned Component to HTML
   - Returns the HTML string

3. **Rendering**: The router uses the `Renderer` from `htmy` to convert Components to HTML strings. This is the same renderer used for full pages, ensuring consistency.

## Best Practices

1. **Keep routes focused**: Each route should return a single, focused fragment
2. **Use path parameters**: Extract dynamic values from the URL, not query strings
3. **Return Components**: Always return Component instances, not raw HTML strings
4. **Handle errors**: Consider error handling in your view functions
5. **Type hints**: Use proper type hints for better IDE support and type checking

## Limitations

- **AJAX-only**: Routes only work with AJAX requests. Full page loads should be handled separately by framework-specific view classes
- **Fragment returns**: Routes return HTML fragments, not full pages
- **Framework-specific**: You need a framework-specific router implementation that extends the base `Router` class
