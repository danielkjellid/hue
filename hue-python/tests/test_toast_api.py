import pytest

from hue import toast
from hue.js import call, unsafe


class TestToastJs:
    def test_a_bare_toast_is_a_title(self):
        assert toast.js.success("Copied to clipboard") == (
            '$toast.success("Copied to clipboard")'
        )

    def test_the_options_are_quoted_rather_than_pasted(self):
        # An apostrophe in a description is a word, not a syntax error in
        # someone's page.
        assert toast.js.info("Back online", description="We'll keep going") == (
            '$toast.info("Back online", { description: "We\'ll keep going" })'
        )

    # duration: given, None, and left out
    def test_a_duration_is_milliseconds(self):
        assert toast.js.info("Back online", duration=2000) == (
            '$toast.info("Back online", { duration: 2000 })'
        )

    def test_no_duration_is_a_toast_that_stays(self):
        assert toast.js.loading("Exporting", duration=None) == (
            '$toast.loading("Exporting", { duration: null })'
        )

    def test_leaving_it_out_leaves_it_to_the_region(self):
        assert "duration" not in toast.js.loading("Exporting")

    # action: both branches
    def test_an_action_is_a_label_and_the_code_it_runs(self):
        # The label is text and is quoted; the expression is code and is not.
        action = ("Retry", call("send"))
        assert toast.js.danger("Could not send", action=action) == (
            '$toast.danger("Could not send", '
            '{ action: { label: "Retry", onClick: () => { send() } } })'
        )

    def test_an_action_may_be_statements(self):
        # on_click takes statements, so an action has to as well: a bare arrow
        # body would make the whole call a syntax error.
        action = ("Undo", unsafe("restored = true; save()"))
        assert toast.js.info("Archived", action=action) == (
            '$toast.info("Archived", { action: { label: "Undo", '
            "onClick: () => { restored = true; save() } } })"
        )

    def test_an_action_must_be_an_expression(self):
        # It is spliced into code, so a string from anywhere would run.
        with pytest.raises(TypeError):
            toast.js.danger("Could not send", action=("Retry", "send()"))  # type: ignore[arg-type]

    def test_without_one_there_is_no_button(self):
        assert "action" not in toast.js.danger("Could not send")

    def test_every_variant_has_a_way_in(self):
        for variant in ("success", "danger", "warning", "info", "loading"):
            assert getattr(toast.js, variant)("x").startswith(f"$toast.{variant}(")
