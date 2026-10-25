import pytest
from hue import html

from hue_fastapi import HueView, Page
from hue_fastapi import assets as assets_module
from hue_fastapi.assets import CHART_JS_URL, CSS_URL, JS_URL, versioned_url
from tests.conftest import STUB_CSS, make_app


async def test_serves_css(client_for):
    """
    The stylesheet is served from the installed package with a CSS content type.
    """
    async with client_for(make_app()) as client:
        response = await client.get(CSS_URL)

    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]
    assert response.text == STUB_CSS


async def test_serves_js(client_for):
    """
    The Alpine bundle is served with a JavaScript content type.
    """
    async with client_for(make_app()) as client:
        response = await client.get(JS_URL)

    assert response.status_code == 200
    assert "javascript" in response.headers["content-type"]


async def test_head_request(client_for):
    """
    HEAD works and still carries the validator, so a client can revalidate
    without downloading the body.
    """
    async with client_for(make_app()) as client:
        response = await client.head(CSS_URL)

    assert response.status_code == 200
    assert response.headers["etag"]


async def test_unknown_asset_paths_are_not_found(client_for):
    """
    Only the two known asset paths are served; the prefix is not a directory.
    """
    async with client_for(make_app()) as client:
        for path in ("/__hue__/unknown.txt", "/some/other/path/"):
            assert (await client.get(path)).status_code == 404


async def test_post_to_an_asset_is_method_not_allowed(client_for):
    """
    Assets are routes, not middleware, so an unsafe method is refused rather
    than falling through to the application.
    """
    async with client_for(make_app()) as client:
        response = await client.post(CSS_URL)

    assert response.status_code == 405


async def test_assets_coexist_with_application_routes(client_for):
    """
    Mounting assets does not shadow the app's own routes.
    """
    app = make_app()

    @app.get("/other/")
    async def other() -> str:
        return "other"

    async with client_for(app) as client:
        assert (await client.get("/other/")).status_code == 200
        assert (await client.get(CSS_URL)).status_code == 200


async def test_an_unversioned_link_revalidates(client_for):
    """
    A quoted ETag and no lifetime, so a link written without the hash never
    holds on to a stale asset but still gets a cheap 304.
    """
    async with client_for(make_app()) as client:
        response = await client.get(CSS_URL)

    assert response.headers["etag"].startswith('"')
    assert response.headers["etag"].endswith('"')
    assert response.headers["cache-control"] == "public, no-cache"


async def test_a_versioned_link_is_cached_for_good(client_for):
    """
    The URL a page links names the content, so it can never change.
    """
    async with client_for(make_app()) as client:
        response = await client.get(versioned_url(CSS_URL))

    assert response.headers["cache-control"] == "public, max-age=31536000, immutable"


async def test_a_page_links_the_versioned_urls(client_for):
    """
    The default page points at hue's own assets by their hashed URLs.
    """

    class Home(HueView):
        async def index(self, request, context):
            return Page(title="Home", body=html.div("Home"))

    async with client_for(make_app(("/home", Home))) as client:
        text = (await client.get("/home/")).text

    assert versioned_url(CSS_URL) in text
    assert versioned_url(JS_URL) in text


async def test_serves_the_chart_bundle(client_for):
    async with client_for(make_app()) as client:
        assert (await client.get(CHART_JS_URL)).status_code == 200


@pytest.mark.parametrize(
    "header_template",
    ["{etag}", "W/{etag}", '"other", {etag}', "*"],
    ids=["exact", "weak", "in-a-list", "star"],
)
async def test_returns_304_on_matching_etag(client_for, header_template):
    """
    Every If-None-Match form RFC 7232 allows is honoured.
    """
    async with client_for(make_app()) as client:
        etag = (await client.get(CSS_URL)).headers["etag"]
        response = await client.get(
            CSS_URL, headers={"If-None-Match": header_template.format(etag=etag)}
        )

    assert response.status_code == 304
    assert response.headers["etag"] == etag


async def test_returns_200_on_non_matching_etag(client_for):
    """
    A stale validator gets the body.
    """
    async with client_for(make_app()) as client:
        response = await client.get(CSS_URL, headers={"If-None-Match": '"stale"'})

    assert response.status_code == 200
    assert response.text == STUB_CSS


async def test_reads_each_asset_once(client_for):
    """
    The file is read from disk once per process, not once per request.
    """
    async with client_for(make_app()) as client:
        await client.get(CSS_URL)
        await client.get(CSS_URL)

    assert set(assets_module._cache) == {CSS_URL}
