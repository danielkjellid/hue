import pytest

from hue import html
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
from hue.js import unsafe
from hue.renderer import render_tree


class TestElement:
    @pytest.mark.parametrize(
        ("tag", "cls"),
        [
            ("a", AnchorElement),
            ("button", ButtonElement),
            ("form", FormElement),
            ("img", ImgElement),
            ("input_", InputElement),
            ("label", LabelElement),
            ("select", SelectElement),
            ("textarea", TextareaElement),
            ("div", Element),
        ],
    )
    def test_each_tag_gets_the_element_that_types_its_attributes(self, tag, cls):
        assert type(getattr(html, tag)()) is cls

    def test_unknown_tag_raises(self):
        with pytest.raises(AttributeError):
            html.nonexistent_tag()

    def test_positional_children_are_content(self):
        assert html.span("a", "b")._children == html.span().content("a", "b")._children

    def test_void_element_rejects_children(self):
        with pytest.raises(TypeError):
            html.input_("nope")
        with pytest.raises(TypeError):
            html.input_().content("nope")

    def test_x_if_refuses_a_string(self):
        # Alpine evaluates it, so it is an expression like x_show's.
        with pytest.raises(TypeError, match="takes an expression"):
            html.template().x_if("open")  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("element", "rendered"),
    [
        (html.a("About").href("/about"), '<a href="/about">About</a>'),
        (html.img().src("/logo.svg").alt("Logo"), '<img src="/logo.svg" alt="Logo"/>'),
        (html.div().data("value", "42"), 'data-value="42"'),
        (html.option("Paid").value("paid").selected(), '<option value="paid" selected'),
        (html.template().x_if(unsafe("open")), '<template x-if="open"'),
        (html.div().x_data({"open": False}), """x-data='{"open": false}'"""),
        (html.div().x_on("click.outside", unsafe("x = 1")), '@click.outside="x = 1"'),
        (html.div().x_bind("class", unsafe("{a: open}")), ':class="{a: open}"'),
        (html.div().x_transition_enter("ease-out"), 'x-transition:enter="ease-out"'),
        (html.form().x_target_away("_top"), 'x-target.away="_top"'),
        (html.form().x_headers({"X-Custom": "v"}), """x-headers='{"X-Custom": "v"}'"""),
        (html.textarea().x_model(unsafe("form.bio")), 'x-model="form.bio"'),
        (html.button().formnoajax(), "formnoajax"),
    ],
    ids=lambda value: value if isinstance(value, str) else "",
)
@pytest.mark.asyncio
async def test_a_modifier_renders_its_attribute(context_args, element, rendered):
    assert rendered in await render_tree(element, context_args=context_args)
