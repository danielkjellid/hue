import pytest

from hue import html
from hue.context import HueContextArgs
from hue.html.element import (
    AnchorElement,
    ButtonElement,
    Element,
    FormElement,
    ImgElement,
    InputElement,
    LabelElement,
    SelectElement,
    TextareaElement,
)
from hue.renderer import render_tree
from hue.ui import Button, Stack, Text


class _MockRequest:
    pass


def _context_args() -> HueContextArgs[_MockRequest]:
    return HueContextArgs(request=_MockRequest(), csrf_token="tok")


# ---------------------------------------------------------------------------
# Element basics
# ---------------------------------------------------------------------------


class TestElement:
    def test_dynamic_tag_returns_element(self):
        el = html.div()
        assert isinstance(el, Element)

    def test_different_tags(self):
        for tag in ("div", "span", "section", "nav", "main"):
            el = getattr(html, tag)()
            assert isinstance(el, Element)

    def test_unknown_tag_raises(self):
        with pytest.raises(AttributeError):
            html.nonexistent_tag()

    def test_class_returns_self(self):
        el = html.div()
        assert el.class_("foo") is el

    def test_attr_returns_self(self):
        el = html.div()
        assert el.attr("data-x", "1") is el


# ---------------------------------------------------------------------------
# Specialized element types
# ---------------------------------------------------------------------------


class TestSpecializedElements:
    def test_form_returns_form_element(self):
        assert isinstance(html.form(), FormElement)

    def test_a_returns_anchor_element(self):
        assert isinstance(html.a(), AnchorElement)

    def test_img_returns_img_element(self):
        assert isinstance(html.img(), ImgElement)

    def test_button_returns_button_element(self):
        assert isinstance(html.button(), ButtonElement)

    def test_select_returns_select_element(self):
        assert isinstance(html.select(), SelectElement)

    def test_textarea_returns_textarea_element(self):
        assert isinstance(html.textarea(), TextareaElement)

    def test_label_returns_label_element(self):
        assert isinstance(html.label(), LabelElement)

    def test_input_returns_input_element(self):
        assert isinstance(html.input_(), InputElement)

    def test_div_remains_generic(self):
        el = html.div()
        assert type(el) is Element


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


class TestElementRendering:
    @pytest.mark.asyncio
    async def test_render_empty_div(self):
        result = await render_tree(html.div(), context_args=_context_args())
        assert "<div" in result
        assert "</div>" in result

    @pytest.mark.asyncio
    async def test_render_with_class(self):
        result = await render_tree(
            html.div().class_("container mx-auto"),
            context_args=_context_args(),
        )
        assert 'class="container mx-auto"' in result

    @pytest.mark.asyncio
    async def test_render_with_id(self):
        result = await render_tree(
            html.div().id("main"),
            context_args=_context_args(),
        )
        assert 'id="main"' in result

    @pytest.mark.asyncio
    async def test_render_with_text_content(self):
        result = await render_tree(
            html.p().content("Hello world"),
            context_args=_context_args(),
        )
        assert "<p" in result
        assert "Hello world" in result
        assert "</p>" in result

    @pytest.mark.asyncio
    async def test_render_with_attr(self):
        result = await render_tree(
            html.div().attr("data-value", "42"),
            context_args=_context_args(),
        )
        assert 'data-value="42"' in result

    @pytest.mark.asyncio
    async def test_render_with_aria(self):
        result = await render_tree(
            html.div().aria_label("Navigation").role("navigation"),
            context_args=_context_args(),
        )
        assert 'aria-label="Navigation"' in result
        assert 'role="navigation"' in result

    @pytest.mark.asyncio
    async def test_render_nested_elements(self):
        result = await render_tree(
            html.div()
            .class_("outer")
            .content(
                html.span().class_("inner").content("Nested"),
            ),
            context_args=_context_args(),
        )
        assert 'class="outer"' in result
        assert 'class="inner"' in result
        assert "Nested" in result

    @pytest.mark.asyncio
    async def test_render_heading(self):
        result = await render_tree(
            html.h1().content("Title"),
            context_args=_context_args(),
        )
        assert "<h1" in result
        assert "Title" in result


# ---------------------------------------------------------------------------
# Specialized element rendering
# ---------------------------------------------------------------------------


class TestSpecializedRendering:
    @pytest.mark.asyncio
    async def test_form_typed_methods(self):
        result = await render_tree(
            html.form()
            .method("POST")
            .action("/login/")
            .class_("w-full")
            .content("form body"),
            context_args=_context_args(),
        )
        assert 'method="POST"' in result
        assert 'action="/login/"' in result
        assert 'class="w-full"' in result

    @pytest.mark.asyncio
    async def test_anchor_typed_methods(self):
        result = await render_tree(
            html.a()
            .href("/about")
            .target("_blank")
            .rel("noopener")
            .content("About"),
            context_args=_context_args(),
        )
        assert 'href="/about"' in result
        assert 'target="_blank"' in result
        assert 'rel="noopener"' in result
        assert "About" in result

    @pytest.mark.asyncio
    async def test_img_typed_methods(self):
        result = await render_tree(
            html.img().src("/photo.jpg").alt("A photo").loading("lazy"),
            context_args=_context_args(),
        )
        assert 'src="/photo.jpg"' in result
        assert 'alt="A photo"' in result
        assert 'loading="lazy"' in result

    @pytest.mark.asyncio
    async def test_button_typed_methods(self):
        result = await render_tree(
            html.button()
            .type("submit")
            .disabled()
            .content("Send"),
            context_args=_context_args(),
        )
        assert 'type="submit"' in result
        assert "disabled" in result
        assert "Send" in result

    @pytest.mark.asyncio
    async def test_textarea_typed_methods(self):
        result = await render_tree(
            html.textarea()
            .name("bio")
            .rows(4)
            .placeholder("Tell us about yourself"),
            context_args=_context_args(),
        )
        assert 'name="bio"' in result
        assert 'rows="4"' in result
        assert 'placeholder="Tell us about yourself"' in result


# ---------------------------------------------------------------------------
# Composition with v2 components
# ---------------------------------------------------------------------------


class TestElementWithV2Components:
    @pytest.mark.asyncio
    async def test_div_wrapping_button(self):
        result = await render_tree(
            html.div()
            .class_("wrapper")
            .content(
                Button().variant("primary").content("Click me"),
            ),
            context_args=_context_args(),
        )
        assert 'class="wrapper"' in result
        assert "<button" in result
        assert "Click me" in result

    @pytest.mark.asyncio
    async def test_form_with_mixed_content(self):
        """Demonstrates the unified DX: typed html elements + v2 components."""
        result = await render_tree(
            html.form()
            .method("POST")
            .action("/login/")
            .class_("w-full")
            .content(
                Stack()
                .direction("vertical")
                .spacing("sm")
                .content(
                    Text("Sign in").variant("title-3"),

                    Button()
                    .variant("primary")
                    .type("submit")
                    .content("Submit"),
                ),
            ),
            context_args=_context_args(),
        )
        assert "<form" in result
        assert 'method="POST"' in result
        assert "Sign in" in result
        assert "<button" in result
        assert "Submit" in result


# ---------------------------------------------------------------------------
# Alpine.js core directives (available on all elements)
# ---------------------------------------------------------------------------


class TestAlpineCoreDirectives:
    @pytest.mark.asyncio
    async def test_x_data(self):
        result = await render_tree(
            html.div().x_data({"open": False}).content("Hello"),
            context_args=_context_args(),
        )
        assert "x-data" in result

    @pytest.mark.asyncio
    async def test_x_show(self):
        result = await render_tree(
            html.div().x_show("open").content("Visible"),
            context_args=_context_args(),
        )
        assert 'x-show="open"' in result

    @pytest.mark.asyncio
    async def test_x_on(self):
        result = await render_tree(
            html.button()
            .type("button")
            .x_on("click", "open = !open")
            .content("Toggle"),
            context_args=_context_args(),
        )
        assert '@click="open = !open"' in result

    @pytest.mark.asyncio
    async def test_x_on_with_modifier(self):
        result = await render_tree(
            html.div().x_on("click.outside", "open = false"),
            context_args=_context_args(),
        )
        assert '@click.outside="open = false"' in result

    @pytest.mark.asyncio
    async def test_x_bind(self):
        result = await render_tree(
            html.div().x_bind("class", "{'active': open}"),
            context_args=_context_args(),
        )
        assert ':class="' in result

    @pytest.mark.asyncio
    async def test_x_transition(self):
        result = await render_tree(
            html.div()
            .x_show("open")
            .x_transition_enter("transition ease-out")
            .x_transition_leave("transition ease-in"),
            context_args=_context_args(),
        )
        assert 'x-show="open"' in result
        assert 'x-transition:enter="transition ease-out"' in result
        assert 'x-transition:leave="transition ease-in"' in result

    @pytest.mark.asyncio
    async def test_x_ref(self):
        result = await render_tree(
            html.div().x_ref("container"),
            context_args=_context_args(),
        )
        assert 'x-ref="container"' in result

    @pytest.mark.asyncio
    async def test_x_init(self):
        result = await render_tree(
            html.div().x_init("console.log('init')"),
            context_args=_context_args(),
        )
        assert "x-init" in result

    @pytest.mark.asyncio
    async def test_alpine_on_v2_component(self):
        """Core Alpine directives work on v2 components too."""
        result = await render_tree(
            Button()
            .variant("primary")
            .x_on("click", "handleClick()")
            .content("Click"),
            context_args=_context_args(),
        )
        assert '@click="handleClick()"' in result
        assert "<button" in result


# ---------------------------------------------------------------------------
# Alpine AJAX — request-originating elements (form, anchor)
# ---------------------------------------------------------------------------


class TestAlpineAjaxRequest:
    @pytest.mark.asyncio
    async def test_form_x_target(self):
        result = await render_tree(
            html.form()
            .method("POST")
            .action("/comment")
            .x_target("comments")
            .content("form body"),
            context_args=_context_args(),
        )
        assert 'x-target="comments"' in result

    @pytest.mark.asyncio
    async def test_form_x_target_away(self):
        result = await render_tree(
            html.form()
            .x_target("login")
            .x_target_away("_top")
            .content("form body"),
            context_args=_context_args(),
        )
        assert 'x-target="login"' in result
        assert 'x-target.away="_top"' in result

    @pytest.mark.asyncio
    async def test_anchor_x_target(self):
        result = await render_tree(
            html.a().href("/page").x_target("content").content("Load"),
            context_args=_context_args(),
        )
        assert 'x-target="content"' in result

    @pytest.mark.asyncio
    async def test_form_x_headers(self):
        result = await render_tree(
            html.form()
            .x_target("results")
            .x_headers({"X-Custom": "value"})
            .content("form body"),
            context_args=_context_args(),
        )
        assert "x-headers" in result

    @pytest.mark.asyncio
    async def test_x_target_not_on_div(self):
        """x_target is not available on generic elements."""
        div = html.div()
        assert not hasattr(div, "x_target")


# ---------------------------------------------------------------------------
# Alpine x-model — form controls only
# ---------------------------------------------------------------------------


class TestAlpineModel:
    @pytest.mark.asyncio
    async def test_select_x_model(self):
        result = await render_tree(
            html.select().name("country").x_model("form.country"),
            context_args=_context_args(),
        )
        assert "x-model" in result

    @pytest.mark.asyncio
    async def test_textarea_x_model(self):
        result = await render_tree(
            html.textarea().name("bio").x_model("form.bio"),
            context_args=_context_args(),
        )
        assert "x-model" in result

    @pytest.mark.asyncio
    async def test_x_model_not_on_div(self):
        """x_model is not available on generic elements."""
        div = html.div()
        assert not hasattr(div, "x_model")

    @pytest.mark.asyncio
    async def test_input_v2_x_model(self):
        """x_model works on v2 input components."""
        from hue.ui import TextInput

        result = await render_tree(
            TextInput().name("email").label("Email").x_model("form.email"),
            context_args=_context_args(),
        )
        assert "x-model" in result


# ---------------------------------------------------------------------------
# Alpine — formnoajax on button elements
# ---------------------------------------------------------------------------


class TestFormNoAjax:
    @pytest.mark.asyncio
    async def test_button_formnoajax(self):
        result = await render_tree(
            html.button()
            .type("submit")
            .formnoajax()
            .content("Full submit"),
            context_args=_context_args(),
        )
        assert "formnoajax" in result

    @pytest.mark.asyncio
    async def test_formnoajax_not_on_div(self):
        """formnoajax is not available on generic elements."""
        div = html.div()
        assert not hasattr(div, "formnoajax")
