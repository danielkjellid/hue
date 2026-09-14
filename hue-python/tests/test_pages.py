"""
The document shell, and in particular the theme contract.

Getting the theme wrong is invisible in a unit test and obvious to every user:
resolve it late and every dark-mode visitor gets a white flash on every
navigation. These pin the parts that prevent that.
"""

import pytest

from hue.pages import create_page_base
from hue.renderer import render_tree
from tests._a11y import assert_no_selector, assert_selector, select, soup

Page = create_page_base(
    css_url="/static/tailwind.css",
    js_url="/static/alpine.js",
    html_title_factory=lambda title: f"{title} · Test",
)


async def render_page(context_args, page_class=Page, **kwargs):
    return await render_tree(
        page_class(title="Hello", body="body", **kwargs), context_args=context_args
    )


def theme_script(html: str) -> str:
    scripts = [s for s in select(html, "head script") if "data-theme" in s.text]
    assert scripts, "no theme script in <head>"
    return scripts[0].text


class TestThemeScript:
    @pytest.mark.asyncio
    async def test_applies_the_theme_before_first_paint(self, context_args):
        html = await render_page(context_args)
        script = soup(html).select_one("head script")
        assert script is not None
        # Blocking: a module or deferred script runs after the first paint,
        # which is the white flash this exists to prevent.
        assert not script.has_attr("type")
        assert not script.has_attr("defer")
        assert not script.has_attr("async")
        assert "data-theme" in script.text

    @pytest.mark.asyncio
    async def test_resolves_system_against_the_os(self, context_args):
        script = theme_script(await render_page(context_args))
        assert "prefers-color-scheme: dark" in script
        assert "'system'" in script

    @pytest.mark.asyncio
    async def test_reads_the_default_storage_key(self, context_args):
        assert '"hue-theme"' in theme_script(await render_page(context_args))

    @pytest.mark.asyncio
    async def test_storage_key_is_configurable(self, context_args):
        page_class = create_page_base(
            css_url="/c.css",
            js_url="/j.js",
            html_title_factory=str,
            theme_storage_key="admin-theme",
        )
        script = theme_script(await render_page(context_args, page_class))
        assert '"admin-theme"' in script

    @pytest.mark.asyncio
    async def test_blocked_site_data_still_honours_the_os(self, context_args):
        # localStorage throws rather than returning null in private modes, so
        # only the stored choice may sit inside the catch: a visitor who blocks
        # site data should still land on their system theme, not on light.
        script = theme_script(await render_page(context_args))
        assert "catch" in script
        catch_body = script.split("catch")[1].split("}")[0]
        assert "prefers-color-scheme" not in catch_body
        assert "setAttribute" not in catch_body


class TestBootstrap:
    @pytest.mark.asyncio
    async def test_passes_csrf_token_and_theme_key_to_alpine(self, context_args):
        html = await render_page(context_args)
        bootstrap = [
            s.text for s in select(html, "script") if "configureAlpine" in s.text
        ]
        assert bootstrap, "no Alpine bootstrap script"
        assert '"csrfToken": "tok"' in bootstrap[0]
        assert '"themeStorageKey": "hue-theme"' in bootstrap[0]

    @pytest.mark.asyncio
    async def test_body_does_not_carry_the_theme(self, context_args):
        # data-theme lives on <html>, set by the head script, so the CSS can
        # match it before Alpine has booted.
        html = await render_page(context_args)
        assert_no_selector(html, "body[data-theme]")
        assert_no_selector(html, "body[\\:data-theme]")
        assert_selector(html, "body.bg-canvas")
