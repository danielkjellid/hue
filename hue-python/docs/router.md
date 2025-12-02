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

Optionally, framework-specific routers can also override:

- `_is_ajax_request()`: Customize AJAX request detection for framework-specific header access
- `_normalize_path()`: Customize path normalization (default strips leading slashes)

## Basic Usage

The router is used within view classes to define AJAX fragment routes. Framework-specific view classes (like `HueView` in Django) integrate the router to handle route registration and request dispatching.

```python
from hue.router import Router
from hue.context import HueContext
from htmy import html

class MyView:
    router = Router[MyRequest]()

    @router.fragment_get("comments/")
    async def list_comments(
        self, request: MyRequest, context: HueContext[MyRequest]
    ) -> html.div:
        return html.div("Comments list")

    @router.fragment_post("comments/")
    async def create_comment(
        self, request: MyRequest, context: HueContext[MyRequest]
    ) -> html.div:
        return html.div("Comment created")
```

## Route Decorators

The router provides decorators for all standard HTTP methods:

- `@router.fragment_get(path)` - AJAX GET requests
- `@router.fragment_post(path)` - AJAX POST requests
- `@router.fragment_put(path)` - AJAX PUT requests
- `@router.fragment_delete(path)` - AJAX DELETE requests
- `@router.fragment_patch(path)` - AJAX PATCH requests

All fragment routes are **AJAX-only** - they require either:

- `X-Requested-With: XMLHttpRequest` header, or
- `X-Alpine-Request: true` header

If a request doesn't have these headers, an `hue.exceptions.AJAXRequiredError` is raised.

## Path Parameters

Path parameters are extracted from the route path and passed as keyword arguments to the view function.

### Path Parameter Syntax

Path parameter syntax is framework-specific. Framework-specific routers implement `_parse_path_params()` to handle their syntax.

For example, Django routers use Django's URL pattern syntax:

```python
@router.fragment_get("comments/<int:comment_id>/")
async def get_comment(
    self,
    request: MyRequest,
    context: HueContext[MyRequest],
    comment_id: int,  # Extracted from path
) -> html.div:
    return html.div(f"Comment {comment_id}")
```

The exact syntax depends on the framework-specific router implementation.

### Multiple Parameters

You can define multiple path parameters:

```python
@router.fragment_get("users/<int:user_id>/posts/<int:post_id>/")
async def get_post(
    self,
    request: HttpRequest,
    context: HueContext[HttpRequest],
    user_id: int,
    post_id: int,
) -> html.div:
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
@router.fragment_get("async/")
async def async_handler(
    self, request: MyRequest, context: HueContext[MyRequest]
) -> html.div:
    return html.div("Async")

# Sync function
@router.fragment_get("sync/")
def sync_handler(
    self, request: MyRequest, context: HueContext[MyRequest]
) -> html.div:
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
    @router.fragment_get("comments/")
    async def list_comments(
        self, request: MyRequest, context: HueContext[MyRequest]
    ) -> html.div:
        comments = ["Comment 1", "Comment 2", "Comment 3"]
        return html.div(
            *[html.p(comment) for comment in comments]
        )

    # Get single comment (fragment with path parameter)
    @router.fragment_get("comments/<int:comment_id>/")
    async def get_comment(
        self,
        request: MyRequest,
        context: HueContext[MyRequest],
        comment_id: int,
    ) -> html.div:
        return html.div(f"Comment {comment_id}")

    # Create comment (fragment)
    @router.fragment_post("comments/")
    async def create_comment(
        self, request: MyRequest, context: HueContext[MyRequest]
    ) -> html.div:
        # Process form data from request
        comment_text = get_comment_from_request(request)
        return html.div(f"Created: {comment_text}")

    # Update comment (fragment)
    @router.fragment_put("comments/<int:comment_id>/")
    async def update_comment(
        self,
        request: MyRequest,
        context: HueContext[MyRequest],
        comment_id: int,
    ) -> html.div:
        return html.div(f"Updated comment {comment_id}")

    # Delete comment (fragment)
    @router.fragment_delete("comments/<int:comment_id>/")
    async def delete_comment(
        self,
        request: MyRequest,
        context: HueContext[MyRequest],
        comment_id: int,
    ) -> html.div:
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
        # E.g. /comments/{comment_id}/replies/{reply_id}/
        # Retuen PathParseResult(path="/comments/{comment_id}/replies/{reply_id}/", param_names=["comment_id", "reply_id"])
        pass

    def _get_context_args(self, request: MyRequest) -> HueContextArgs[MyRequest]:
        """Extract framework-specific context."""
        return HueContextArgs[MyRequest](
            request=request,
            csrf_token=get_csrf_token(request),  # Framework-specific
        )

    # Optional: Override if needed for framework-specific header access
    # def _is_ajax_request(self, request: MyRequest) -> bool:
    #     return request.headers.get("X-Requested-With") == "XMLHttpRequest"
```

### Required Methods

1. **`_parse_path_params(path: str) -> PathParseResult`**

   - Parse the path to extract parameter names
   - Return a `PathParseResult` with the final path pattern and parameter names
   - The path pattern should be in your framework's URL pattern format

2. **`_get_context_args(request: T_Request) -> HueContextArgs[T_Request]`**
   - Extract the request object and CSRF token
   - Return a `HueContextArgs` TypedDict

### Optional Methods

3. **`_is_ajax_request(request: T_Request) -> bool`**

   - Override if your framework has a different way to access request headers
   - Default implementation checks for `X-Requested-With: XMLHttpRequest` or `X-Alpine-Request: true` headers

4. **`_normalize_path(path: str) -> str`**
   - Override to customize path normalization
   - Default implementation strips leading slashes (e.g., `"/path/"` becomes `"path/"`)

## Public API

The router provides a few public methods and properties:

- **`routes`**: A property that returns a copy of all registered routes (useful for debugging or introspection)
- **`render(component, request)`**: An async method that renders a Component to an HTML string using the router's context

## How It Works

1. **Route Registration**: When you use a decorator like `@router.fragment_get("path/")`, the router:

   - Normalizes the path
   - Parses path parameters
   - Wraps the view function
   - Stores the route

2. **Request Handling**: When a request comes in:

   - The framework-specific view (e.g., `HueView`) finds the matching route
   - Calls the wrapped view function with the request and path parameters
   - The wrapped function validates AJAX headers (raises `AJAXRequiredError` if not AJAX)
   - Creates a `HueContext` and calls the original view function
   - Renders the returned Component to HTML using the `render()` method
   - Returns the HTML string

3. **Rendering**: The router uses the `render()` method which internally calls `render_tree()` from `hue.renderer` to convert Components to HTML strings. This is the same renderer used for full pages, ensuring consistency.

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
