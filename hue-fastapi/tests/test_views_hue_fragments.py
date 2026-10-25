import pytest
from hue import html
from hue.context import HueContext
from starlette.requests import Request

from hue_fastapi import HueFragmentsView, Router
from tests.conftest import AJAX_HEADERS, make_app


class CommentFragments(HueFragmentsView):
    router = Router[Request]()

    @router.fragment_get("comments/")
    async def list_comments(self, request: Request, context: HueContext[Request]):
        return html.div("Comments list")

    @router.fragment_post("comments/")
    async def create_comment(self, request: Request, context: HueContext[Request]):
        return html.div("Comment created")


async def test_fragments_are_served(client_for):
    """
    A fragments view serves its routes and nothing else.
    """
    async with client_for(make_app(("/api", CommentFragments))) as client:
        listing = await client.get("/api/comments/", headers=AJAX_HEADERS)
        created = await client.post("/api/comments/", headers=AJAX_HEADERS)

    assert "Comments list" in listing.text
    assert "Comment created" in created.text
    assert "<!DOCTYPE html>" not in listing.text


async def test_there_is_no_index_route(client_for):
    """
    Without an index there is no page at the mount point.
    """
    async with client_for(make_app(("/api", CommentFragments))) as client:
        response = await client.get("/api/")

    assert response.status_code == 404


def test_a_view_without_a_router_is_rejected():
    """
    A fragments view with no routes is a mistake worth catching at build time.
    """

    class NoRouter(HueFragmentsView):
        pass

    with pytest.raises(ValueError, match="must define a 'router' attribute"):
        _ = NoRouter.api_router
