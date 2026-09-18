import pytest
from django.http import HttpResponse, HttpResponseRedirect
from django.test import RequestFactory
from hue.toast import toast

from hue_django.middleware import SESSION_KEY, HueToastMiddleware


class _Session(dict):
    """
    Enough of Django's session for a middleware to put a toast in.
    """


@pytest.fixture
def rf():
    return RequestFactory()


def _request(rf, session=None):
    request = rf.get("/invoices/")
    request.session = _Session(session or {})
    return request


class TestCarryingToastsAcrossARedirect:
    def test_a_redirect_leaves_its_toast_in_the_session(self, rf):
        def get_response(request):
            toast.success("Saved", description="Three fields changed")
            return HttpResponseRedirect("/invoices/")

        request = _request(rf)
        HueToastMiddleware(get_response)(request)

        stored = request.session[SESSION_KEY]
        assert [message["title"] for message in stored] == ["Saved"]
        assert stored[0]["description"] == "Three fields changed"

    def test_the_next_request_picks_it_up_and_the_session_lets_go(self, rf):
        seen: list[str] = []

        def get_response(request):
            seen.extend(message.title for message in toast.drain())
            return HttpResponse("The page after the redirect")

        request = _request(
            rf, {SESSION_KEY: [{"variant": "success", "title": "Saved"}]}
        )
        HueToastMiddleware(get_response)(request)

        assert seen == ["Saved"]
        # Left in the session it would arrive again on the next page.
        assert SESSION_KEY not in request.session

    def test_a_toast_something_rendered_is_not_stored_as_well(self, rf):
        def get_response(request):
            toast.success("Sent")
            # Whatever rendered it - a region on a page, the router behind a
            # fragment - takes it off the queue.
            toast.drain()
            return HttpResponse("Rendered")

        request = _request(rf)
        HueToastMiddleware(get_response)(request)

        assert SESSION_KEY not in request.session

    def test_a_request_that_raised_nothing_writes_nothing(self, rf):
        request = _request(rf)
        HueToastMiddleware(lambda r: HttpResponse("Quiet"))(request)

        assert SESSION_KEY not in request.session

    def test_it_opens_the_queue_for_a_plain_view(self, rf):
        # Without the middleware, toast.success() outside a hue router has
        # nowhere to go and says so.
        raised: list[bool] = []

        def get_response(request):
            toast.info("From a plain Django view")
            raised.append(True)
            return HttpResponse("ok")

        HueToastMiddleware(get_response)(_request(rf))
        assert raised == [True]

    def test_a_response_that_raises_still_closes_the_queue(self, rf):
        def get_response(request):
            toast.info("Half done")
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            HueToastMiddleware(get_response)(_request(rf))

        # The queue is closed, so the next request starts clean rather than
        # inheriting a half-finished one.
        with pytest.raises(RuntimeError, match="no request to carry it"):
            toast.success("After the fall")
