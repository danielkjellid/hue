from dataclasses import dataclass

import pytest
from pydantic import BaseModel, Field

from hue import html
from hue.js import ajax, call, unsafe
from hue.ui import Button, Card, MenuItem, Stack, TextInput


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        (("sendInvoice", 2048), "sendInvoice(2048)"),
        (("greet", "O'Hara"), 'greet("O\'Hara")'),
        (("$store.cart.add", 7), "$store.cart.add(7)"),
        # An expression goes in as written, alone or at any depth: quoted, the
        # one way of passing a variable would be the one way that cannot work.
        (("note", unsafe("selected"), "archived", 3), 'note(selected, "archived", 3)'),
        (
            ("save", {"ids": unsafe("selected"), "tags": [unsafe("t")]}),
            'save({"ids": selected, "tags": [t]})',
        ),
        (
            ("f", {"page": 2, "flags": [True, None], "q": "O'Hara"}),
            'f({"page": 2, "flags": [true, null], "q": "O\'Hara"})',
        ),
    ],
)
def test_call_quotes_its_arguments(args, expected):
    # The point of it: the short way to write an action is the safe one.
    assert call(*args) == expected


def test_call_refuses_a_function_that_is_an_expression():
    # Otherwise there would be nothing left to quote.
    with pytest.raises(ValueError, match="not a function name"):
        call("alert(1);//", 1)


@dataclass
class _ArchiveData:
    reason: str
    notify: bool | None = None
    ids: object = None


class _ArchiveModel(BaseModel):
    reason: str
    notify: bool | None = None
    send_at: str = Field("now", alias="sendAt")


class TestAjax:
    @pytest.mark.parametrize(
        ("kwargs", "expected"),
        [
            # sync, so the toast region a route's toast arrives in is updated too.
            (
                {"method": "delete", "target": "invoices"},
                '{"method": "delete", "target": "invoices", "sync": true})',
            ),
            # It defaults to GET, like $ajax itself.
            ({"target": "t"}, '{"method": "get", "target": "t", "sync": true})'),
            (
                {
                    "method": "post",
                    "target": ["rows", "summary"],
                    "body": {"reason": 'a "duplicate"', "ids": unsafe("selected")},
                },
                '"target": "rows summary", "sync": true, '
                '"body": {"reason": "a \\"duplicate\\"", "ids": selected}})',
            ),
            # A None is left out so the default applies: $ajax would send "null".
            (
                {"method": "post", "target": "t", "body": {"q": None, "page": 2}},
                '"body": {"page": 2}})',
            ),
            # asdict would deep-copy the expression into a plain str.
            (
                {
                    "method": "post",
                    "target": "t",
                    "body": _ArchiveData("dup", ids=unsafe("selected")),
                },
                '"body": {"reason": "dup", "ids": selected}})',
            ),
            # The route validates the form by alias, so that is the field's name.
            (
                {
                    "method": "post",
                    "target": "t",
                    "body": _ArchiveModel(reason="dup", notify=True),
                },
                '"body": {"reason": "dup", "notify": true, "sendAt": "now"}})',
            ),
        ],
        ids=["no body", "get", "quoted body", "none", "dataclass", "model"],
    )
    def test_a_request_is_written_with_every_value_quoted(self, kwargs, expected):
        request = ajax("/invoices/2048/", **kwargs)
        assert request.startswith('$ajax("/invoices/2048/", {')
        assert request.endswith(expected)

    @pytest.mark.parametrize(
        ("kwargs", "error", "match"),
        [
            (
                {"method": "post", "target": "t", "body": [("q", 1)]},
                TypeError,
                "mapping, a dataclass",
            ),
            # "GET" would slip past the check on a GET's body, and still be one.
            (
                {"method": "GET", "target": "t", "body": {"q": 1}},
                ValueError,
                "not a method",
            ),
            # $ajax would turn it into the query string, which no body model reads.
            ({"target": "t", "body": {"q": "contoso"}}, ValueError, "query string"),
            # $ajax would fall back to the id of whatever runs it, often none.
            ({"target": ""}, ValueError, None),
            ({"target": []}, ValueError, None),
            ({"target": ["rows summary"]}, ValueError, None),
        ],
    )
    def test_a_request_that_cannot_work_is_refused(self, kwargs, error, match):
        with pytest.raises(error, match=match):
            ajax("/invoices/", **kwargs)


_AJAX_EVENTS = (
    "before send redirect success error sent missing merge merged after".split()
)


class TestModifiersRefuseStrings:
    @pytest.mark.parametrize(
        ("component", "modifier", "args"),
        [
            (Button, "x_on", ("click", "open = true")),
            (Button, "x_bind", ("aria-expanded", "open")),
            (Button, "x_show", ("open",)),
            (Button, "x_text", ("label",)),
            (Button, "x_html", ("body",)),
            (Button, "x_effect", ("open && go()",)),
            (Button, "x_init", ("go()",)),
            (Button, "x_trap", ("open",)),
            (Button, "x_anchor", ("$refs.trigger",)),
            (Button, "on_click", ("send(1)",)),
            (TextInput, "x_model", ("q; window.x++",)),
            (html.form, "x_target_dynamic", ("'rows'",)),
            # Alpine evaluates every @ajax:* handler, so these are code too.
            *[(Button, f"ajax_{event}", ("done = true",)) for event in _AJAX_EVENTS],
        ],
    )
    def test_a_plain_string_is_refused(self, component, modifier, args):
        # There is no escaping that makes code safe, so the only way in is to
        # say so.
        with pytest.raises(TypeError, match="takes an expression"):
            getattr(component(), modifier)(*args)

    def test_an_expression_goes_through(self):
        attrs = (
            Button()
            .x_on("click", unsafe("open = true"))
            .ajax_success(unsafe("done = true"))
            ._get_base_html_attrs()
        )
        assert attrs["@click"] == "open = true"
        assert attrs["@ajax:success"] == "done = true"


class TestOnClick:
    def test_it_is_only_on_what_a_browser_treats_as_a_control(self):
        # A click handler on a div is not reachable by keyboard and is
        # announced as nothing in particular, so the sugar is not there.
        assert hasattr(Button(), "on_click")
        assert hasattr(MenuItem(), "on_click")
        assert not hasattr(Card(), "on_click")
        assert not hasattr(Stack(), "on_click")

    def test_several_run_in_order(self):
        attrs = (
            Button()
            .on_click(call("send", 1), unsafe("open = false"))
            ._get_base_html_attrs()
        )
        assert attrs["@click"] == "send(1); open = false"

    def test_a_disabled_control_drops_its_handler(self):
        # Enter on a focused, aria-disabled control is still a click.
        button = Button().on_click(call("send", 1))
        assert "@click" not in button._get_clickable_attrs(disabled=True)
        assert button._get_clickable_attrs(disabled=False)["@click"] == "send(1)"
