from typing import Any, Final

from hue.scope import request_scope
from hue.toast import ToastMessage, toast
from starlette.types import ASGIApp, Message, Receive, Scope, Send

# Where the toasts raised before a redirect wait for the page after it.
SESSION_KEY: Final = "hue_toasts"


def _load(session: dict[str, Any] | None) -> None:
    """
    Hand back whatever the last request left behind, oldest first.
    """
    stored = session.pop(SESSION_KEY, None) if session is not None else None
    if stored:
        toast.restore(ToastMessage.from_dict(data) for data in stored)


def _save(session: dict[str, Any] | None) -> None:
    """
    Keep what nothing rendered, for the next request to show.

    A page empties the queue through its region and a fragment through the
    router, so what is left here was raised by something that returned no
    markup at all, a redirect most often.
    """
    pending = toast.drain()
    if pending and session is not None:
        session[SESSION_KEY] = [message.as_dict() for message in pending]


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
            _load(session)

            # Saved as the response starts rather than after it: the session
            # middleware outside writes its cookie at that same moment.
            async def send_and_save(message: Message) -> None:
                if message["type"] == "http.response.start":
                    _save(session)
                await send(message)

            await self.app(scope, receive, send_and_save)
