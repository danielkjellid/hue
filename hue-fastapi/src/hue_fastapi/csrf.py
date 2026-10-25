import secrets
from dataclasses import dataclass
from typing import Final, Literal

from fastapi import HTTPException
from itsdangerous import BadData, URLSafeSerializer
from starlette.requests import Request
from starlette.responses import Response

from hue_fastapi.config import get_config

SAFE_METHODS: Final = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})
FORM_CONTENT_TYPES: Final = (
    "application/x-www-form-urlencoded",
    "multipart/form-data",
)
# Fixed rather than settings: hue's Alpine bundle always sends this header,
# and a table strips this field from the state it echoes into links.
CSRF_HEADER: Final = "X-CSRFToken"
CSRF_FORM_FIELD: Final = "csrf_token"

_STATE_TOKEN: Final = "hue_csrf_token"


@dataclass(frozen=True, slots=True)
class CsrfConfig:
    """
    Signed double submit cookie protection.

    Starlette ships none of this. The signature means the server accepts only
    tokens it minted itself. It does not tie a token to one browser, so with
    cookie_secure the cookie takes the __Host- prefix, which a browser only
    accepts over HTTPS from the host itself: a sibling subdomain cannot plant
    one. Without it, serve the app from a domain no untrusted subdomain shares.

    AJAX requests carry the token in the header hue's Alpine bundle sends.
    Forms that post without AJAX carry it in a hidden field instead, via
    ui.CsrfTokenInput.
    """

    secret_key: str
    cookie_name: str = "csrftoken"
    cookie_secure: bool = False
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    max_age: int = 60 * 60 * 24 * 7 * 52

    @property
    def _cookie(self) -> str:
        return f"__Host-{self.cookie_name}" if self.cookie_secure else self.cookie_name

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

        cookie_token = request.cookies.get(self._cookie)
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
        if token is None or token == request.cookies.get(self._cookie):
            return

        response.set_cookie(
            key=self._cookie,
            value=token,
            max_age=self.max_age,
            path="/",
            secure=self.cookie_secure,
            # The page carries the token; JavaScript never reads the cookie.
            httponly=True,
            samesite=self.cookie_samesite,
        )

    async def verify(self, request: Request) -> bool:
        cookie_token = request.cookies.get(self._cookie)
        if not cookie_token or not self._is_valid(cookie_token):
            return False

        submitted = request.headers.get(CSRF_HEADER)

        if not submitted:
            content_type = request.headers.get("content-type", "")
            # Only touch the form for form-shaped bodies. Calling form() on a
            # JSON request consumes the stream that hue is about to read.
            if content_type.startswith(FORM_CONTENT_TYPES):
                form = await request.form()
                value = form.get(CSRF_FORM_FIELD)
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
