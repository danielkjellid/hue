from hue.scope import request_scope
from hue.toast import keep_in_session, restore_from_session
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class HueRequestMiddleware:
    """
    Open hue's request-scoped state for the whole request, and carry toasts
    across a redirect.

    The toast queue and the list shortcuts.use() writes to are opened here as
    well as in the router, so both work in a plain FastAPI endpoint and not
    only inside a hue route. A toast raised before a redirect waits in the
    session and arrives with the page after it, which needs Starlette's
    SessionMiddleware outside this one:

        app.add_middleware(HueRequestMiddleware)
        app.add_middleware(SessionMiddleware, secret_key=...)
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        session = scope.get("session")
        with request_scope():
            restore_from_session(session)

            # Saved as the response starts rather than after it: the session
            # middleware outside writes its cookie at that same moment.
            async def send_and_save(message: Message) -> None:
                if message["type"] == "http.response.start":
                    keep_in_session(session)
                await send(message)

            await self.app(scope, receive, send_and_save)
