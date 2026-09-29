import pytest

from hue.js import Expression, call, close, unsafe
from hue.ui import Button, Card, MenuItem, Stack


class TestExpressions:
    def test_unsafe_vouches_for_source_as_written(self):
        assert unsafe("open = !open") == "open = !open"
        assert isinstance(unsafe("open"), Expression)

    def test_call_quotes_its_arguments(self):
        # The point of it: the short way to write an action is the safe one.
        assert call("sendInvoice", 2048) == "sendInvoice(2048)"
        assert call("copy", "ada@example.com") == 'copy("ada@example.com")'
        assert call("greet", "O'Hara") == 'greet("O\'Hara")'

    def test_call_refuses_a_function_that_is_an_expression(self):
        # Otherwise there would be nothing left to quote.
        with pytest.raises(ValueError, match="not a function name"):
            call("alert(1);//", 1)

    def test_close_is_the_way_out_of_an_overlay(self):
        # Every overlay puts one in scope, so the common action says what it
        # does rather than vouching for a string.
        assert close() == "close()"
        assert isinstance(close(), Expression)

    def test_call_takes_a_path_to_a_function(self):
        assert call("$store.cart.add", 7) == "$store.cart.add(7)"


class TestModifiersRefuseStrings:
    @pytest.mark.parametrize(
        ("modifier", "args"),
        [
            ("x_on", ("click", "open = true")),
            ("x_bind", ("aria-expanded", "open")),
            ("x_show", ("open",)),
            ("x_text", ("label",)),
            ("x_html", ("body",)),
            ("x_effect", ("open && go()",)),
            ("x_init", ("go()",)),
            ("x_trap", ("open",)),
            ("x_anchor", ("$refs.trigger",)),
        ],
    )
    def test_a_plain_string_is_refused(self, modifier, args):
        # There is no escaping that makes code safe, so the only way in is to
        # say so.
        with pytest.raises(TypeError, match="takes an expression"):
            getattr(Button(), modifier)(*args)

    def test_an_expression_goes_through(self):
        attrs = Button().x_on("click", unsafe("open = true"))._get_base_html_attrs()
        assert attrs["@click"] == "open = true"


class TestOnClick:
    def test_it_is_only_on_what_a_browser_treats_as_a_control(self):
        # A click handler on a div is not reachable by keyboard and is
        # announced as nothing in particular, so the sugar is not there.
        assert hasattr(Button(), "on_click")
        assert hasattr(MenuItem(), "on_click")
        assert not hasattr(Card(), "on_click")
        assert not hasattr(Stack(), "on_click")

    def test_it_is_a_click_handler(self):
        attrs = Button().on_click(call("send", 1))._get_base_html_attrs()
        assert attrs["@click"] == "send(1)"

    def test_several_run_in_order(self):
        attrs = (
            Button()
            .on_click(call("send", 1), unsafe("open = false"))
            ._get_base_html_attrs()
        )
        assert attrs["@click"] == "send(1); open = false"

    def test_a_string_is_refused(self):
        with pytest.raises(TypeError, match="takes an expression"):
            Button().on_click("send(1)")


def test_an_expression_argument_goes_in_as_written():
    # Quoting it back into a string would make the one way of passing a
    # variable the one way that cannot work.
    assert call("remove", unsafe("selected")) == "remove(selected)"


def test_everything_else_is_still_quoted():
    assert call("note", unsafe("selected"), "archived", 3) == (
        'note(selected, "archived", 3)'
    )
