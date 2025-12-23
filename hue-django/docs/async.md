# Async Views and Sync Operations

Hue Django views support both sync and async view functions. The Django router automatically handles the differences, wrapping sync functions with `sync_to_async` for proper ASGI compatibility.

## Sync vs Async View Functions

You can define view functions as either sync or async:

```python
class MyView(HueView):
    router = Router[HttpRequest]()

    # ✅ Async view function
    @router.fragment_get("async-example/")
    async def async_view(
        self, request: HttpRequest, context: HueContext[HttpRequest]
    ):
        return html.p("Async view")

    # ✅ Sync view function (automatically wrapped with sync_to_async)
    @router.fragment_get("sync-example/")
    def sync_view(
        self, request: HttpRequest, context: HueContext[HttpRequest]
    ):
        return html.p("Sync view")
```

Both work correctly. Sync functions are automatically wrapped with `sync_to_async` by the Django router.

## The Sync-in-Async Problem

While sync view functions work automatically, **calling sync code from inside async view functions** still requires explicit handling. Django's ORM, authentication, sessions, and many other built-in features are **synchronous**. When you call these from an async view without proper handling, it can cause:

- Connection handling issues
- Duplicate requests
- Malformed responses
- Unexpected behavior

### Example of the Problem

```python
from django.contrib.auth import authenticate, login

class LoginView(HueView):
    router = Router[HttpRequest]()

    @router.fragment_post("authenticate/")
    async def authenticate(
        self, request: HttpRequest, context: HueContext[HttpRequest], body: LoginForm
    ):
        # ❌ WRONG: Calling sync functions directly in async context
        user = authenticate(request, username=body.email, password=body.password)
        if user:
            login(request, user)
            return html.p("Success")
        return html.p("Failed")
```

This can cause the browser to receive malformed responses, leading to duplicate requests or other issues.

## The Solution: `sync_to_async`

Use Django's `sync_to_async` wrapper to properly call synchronous code from async views:

```python
from asgiref.sync import sync_to_async
from django.contrib.auth import authenticate, login

class LoginView(HueView):
    router = Router[HttpRequest]()

    @router.fragment_post("authenticate/")
    async def authenticate(
        self, request: HttpRequest, context: HueContext[HttpRequest], body: LoginForm
    ):
        # ✅ CORRECT: Wrap sync functions with sync_to_async
        user = await sync_to_async(authenticate)(
            request, username=body.email, password=body.password
        )
        if user:
            await sync_to_async(login)(request, user)
            return html.p("Success")
        return html.p("Failed")
```

## Common Operations That Need `sync_to_async`

### Authentication

```python
from asgiref.sync import sync_to_async
from django.contrib.auth import authenticate, login, logout

# Authenticate user
user = await sync_to_async(authenticate)(request, username=email, password=password)

# Log user in
await sync_to_async(login)(request, user)

# Log user out
await sync_to_async(logout)(request)
```

### ORM Queries

```python
from asgiref.sync import sync_to_async

# Single object
user = await sync_to_async(User.objects.get)(pk=user_id)

# QuerySet (need to evaluate it)
@sync_to_async
def get_posts():
    return list(Post.objects.filter(published=True))

posts = await get_posts()

# Or use Django's async ORM methods (Django 4.1+)
user = await User.objects.aget(pk=user_id)
posts = [post async for post in Post.objects.filter(published=True)]
```

### Session Operations

```python
from asgiref.sync import sync_to_async

# Set session data
@sync_to_async
def set_session_data(request, key, value):
    request.session[key] = value

await set_session_data(request, "cart_id", cart.id)

# Get session data
@sync_to_async
def get_session_data(request, key, default=None):
    return request.session.get(key, default)

cart_id = await get_session_data(request, "cart_id")
```

### Model Save/Delete

```python
from asgiref.sync import sync_to_async

# Save model
comment = Comment(content=body.content, user=user)
await sync_to_async(comment.save)()

# Delete model
await sync_to_async(comment.delete)()
```

## Creating Reusable Async Wrappers

For commonly used operations, create reusable async wrappers:

```python
# utils/async_auth.py
from asgiref.sync import sync_to_async
from django.contrib.auth import authenticate as django_authenticate
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout


async def authenticate(request, **credentials):
    """Async wrapper for Django's authenticate function."""
    return await sync_to_async(django_authenticate)(request, **credentials)


async def login(request, user):
    """Async wrapper for Django's login function."""
    await sync_to_async(django_login)(request, user)


async def logout(request):
    """Async wrapper for Django's logout function."""
    await sync_to_async(django_logout)(request)
```

Then use them in your views:

```python
from myapp.utils.async_auth import authenticate, login

class LoginView(HueView):
    router = Router[HttpRequest]()

    @router.fragment_post("authenticate/")
    async def do_authenticate(
        self, request: HttpRequest, context: HueContext[HttpRequest], body: LoginForm
    ):
        user = await authenticate(request, username=body.email, password=body.password)
        if user:
            await login(request, user)
            return html.p("Success")
        return html.p("Failed")
```

## Using Django's Native Async Support

Django 4.1+ provides native async versions of many ORM methods:

```python
# Instead of sync_to_async wrappers, use Django's async methods
user = await User.objects.aget(pk=user_id)
exists = await Post.objects.filter(published=True).aexists()
count = await Comment.objects.acount()

# Async iteration
async for post in Post.objects.filter(published=True):
    process(post)
```

See Django's [async documentation](https://docs.djangoproject.com/en/stable/topics/async/) for the full list of async-compatible methods.

## Decorator Alternative

For functions with multiple sync operations, use `sync_to_async` as a decorator:

```python
from asgiref.sync import sync_to_async

@sync_to_async
def process_order(request, order_id):
    """This entire function runs in a sync context."""
    order = Order.objects.get(pk=order_id)
    order.status = "processing"
    order.save()

    # Send notification
    order.user.email_user("Order Processing", "Your order is being processed.")

    return order

class OrderView(HueView):
    router = Router[HttpRequest]()

    @router.fragment_post("orders/<int:order_id>/process/")
    async def process(
        self,
        request: HttpRequest,
        context: HueContext[HttpRequest],
        order_id: int,
    ):
        order = await process_order(request, order_id)
        return html.div(f"Order {order.id} is now processing")
```

## Returning Redirects and HttpResponse

Fragment handlers can return Django `HttpResponse` objects directly, including redirects. These are passed through without rendering:

```python
from asgiref.sync import sync_to_async
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login

class LoginView(HueView):
    router = Router[HttpRequest]()

    @router.fragment_post("authenticate/")
    async def do_authenticate(
        self, request: HttpRequest, context: HueContext[HttpRequest], body: LoginForm
    ):
        user = await sync_to_async(authenticate)(
            request, username=body.email, password=body.password
        )
        if user:
            await sync_to_async(login)(request, user)
            return redirect("/dashboard/")  # Passed through directly

        return HueResponse(
            target="login-form",
            status_code=401,
            component=ui.Callout("Invalid credentials", variant="error"),
        )
```

Any object with a `status_code` attribute (like `HttpResponse`, `HttpResponseRedirect`, `JsonResponse`) is detected and passed through directly to the client.

**Note:** Redirects from AJAX requests may not work as expected in all browsers. The browser follows the redirect, but the response is still handled by JavaScript. Consider returning a success fragment and handling the redirect on the client side if needed.

## Debugging Tips

If you encounter issues like duplicate requests or malformed responses:

1. **Check for unwrapped sync calls**: Any Django ORM, auth, or session operation needs `sync_to_async`

2. **Add debug logging**: Print statements can help identify where the issue occurs:

   ```python
   async def my_handler(self, request, context):
       print("Handler started")
       user = await sync_to_async(authenticate)(request, **creds)
       print("Authentication completed")
       # ...
   ```

3. **Check browser network tab**: Look for duplicate requests to the same endpoint

4. **Verify AJAX headers**: Ensure your frontend is sending proper AJAX headers (see [AJAX Requirements](./views.md#ajax-requirements))

## Summary

| Operation              | Sync (❌ in async views)     | Async (✅)                                                                       |
| ---------------------- | ---------------------------- | -------------------------------------------------------------------------------- |
| `authenticate()`       | `authenticate(request, ...)` | `await sync_to_async(authenticate)(request, ...)`                                |
| `login()`              | `login(request, user)`       | `await sync_to_async(login)(request, user)`                                      |
| `Model.objects.get()`  | `User.objects.get(pk=1)`     | `await User.objects.aget(pk=1)` or `await sync_to_async(User.objects.get)(pk=1)` |
| `model.save()`         | `obj.save()`                 | `await sync_to_async(obj.save)()` or `await obj.asave()`                         |
| `request.session[key]` | `request.session["x"] = y`   | Use `@sync_to_async` decorated function                                          |

Remember: **When in doubt, wrap it with `sync_to_async`**.
