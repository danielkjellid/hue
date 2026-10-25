import secrets
from dataclasses import dataclass
from typing import Final, Literal

from fastapi import HTTPException
from itsdangerous import BadData, URLSafeSerializer
from starlette.requests import Request
from starlette.responses import Response

from hue_fastapi.config import get_config
from hue_fastapi.router import FORM_CONTENT_TYPES

SAFE_METHODS: Final = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})

_STATE_TOKEN: Final = "hue_csrf_token"


@dataclass(frozen=True, slots=True)
class CsrfConfig:
    """
    Signed double submit cookie protection.

    Starlette ships none of this. The signature means the server accepts only
    tokens it minted itself. It does not tie a token to one browser, so a
    sibling subdomain that can set cookies can still plant a token it fetched
    from the site: serve the app from a domain no untrusted subdomain shares.

    The header name matches what hue's Alpine bundle sends, so AJAX requests are
    covered without any work in the page. Forms that post without AJAX carry the
    token in a hidden field instead, via ui.CsrfTokenInput.
    """

    secret_key: str
    cookie_name: str = "csrftoken"
    header_name: str = "X-CSRFToken"
    form_field: str = "csrf_token"
    cookie_secure: bool = False
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    max_age: int = 60 * 60 * 24 * 7 * 52

    def _serializer(self) -> URLSafeSerializer:
        return URLSafeSerializer(self.secret_key, salt="hue.csrf")

    def _is_valid(self, token: str) -> bool:
        try:
            self._serializer().loads(token)
        except BadData:
            return False
        return True

    def get_token(self, request: Request) -> str:
        """
        The token this request should render into the page.

        Generated on first read and remembered on the request, so the very first
        visit, which arrives with no cookie, still embeds the same value the
        response is about to set. Reading it is what schedules the cookie.
        """
        existing: str | None = getattr(request.state, _STATE_TOKEN, None)
        if existing is not None:
            return existing

        cookie_token = request.cookies.get(self.cookie_name)
        if cookie_token and self._is_valid(cookie_token):
            token = cookie_token
        else:
            token = self._serializer().dumps(secrets.token_urlsafe(32))

        setattr(request.state, _STATE_TOKEN, token)
        return token

    def apply(self, request: Request, response: Response) -> None:
        """
        Set the cookie when this request minted a new token, which is any
        token that is not the cookie it came with.
        """
        token: str | None = getattr(request.state, _STATE_TOKEN, None)
        if token is None or token == request.cookies.get(self.cookie_name):
            return

        response.set_cookie(
            key=self.cookie_name,
            value=token,
            max_age=self.max_age,
            path="/",
            secure=self.cookie_secure,
            # The page carries the token; JavaScript never reads the cookie.
            httponly=True,
            samesite=self.cookie_samesite,
        )

    async def verify(self, request: Request) -> bool:
        cookie_token = request.cookies.get(self.cookie_name)
        if not cookie_token or not self._is_valid(cookie_token):
            return False

        submitted = request.headers.get(self.header_name)

        if not submitted:
            content_type = request.headers.get("content-type", "")
            # Only touch the form for form-shaped bodies. Calling form() on a
            # JSON request consumes the stream that hue is about to read.
            if content_type.startswith(FORM_CONTENT_TYPES):
                form = await request.form()
                value = form.get(self.form_field)
                submitted = value if isinstance(value, str) else None

        if not submitted:
            return False

        # Bytes, since compare_digest refuses a str with anything non-ASCII,
        # which would make a junk header a 500 rather than a 403.
        return secrets.compare_digest(submitted.encode(), cookie_token.encode())


async def csrf_protect(request: Request) -> None:
    """
    FastAPI dependency enforcing CSRF on unsafe methods.

    Attached automatically to every non-safe hue route. Apps can depend on it
    directly for their own endpoints.
    """
    config = get_config(request.app)
    if config.csrf is None or request.method in SAFE_METHODS:
        return

    if not await config.csrf.verify(request):
        raise HTTPException(status_code=403, detail="CSRF verification failed")
