import pytest

from hue import toast
from hue.js import call, unsafe


class TestToastJs:
    @pytest.mark.parametrize(
        ("call_", "expected"),
        [
            # Left out, the duration and the action are the region's to decide.
            (lambda: toast.js.success("Copied"), '$toast.success("Copied")'),
            (lambda: toast.js.warning("Careful"), '$toast.warning("Careful")'),
            # An apostrophe in a description is a word, not a syntax error in
            # someone's page.
            (
                lambda: toast.js.info("Back online", description="We'll keep going"),
                '$toast.info("Back online", { description: "We\'ll keep going" })',
            ),
            (
                lambda: toast.js.info("Back online", duration=2000),
                '$toast.info("Back online", { duration: 2000 })',
            ),
            # No duration is a toast that stays.
            (
                lambda: toast.js.loading("Exporting", duration=None),
                '$toast.loading("Exporting", { duration: null })',
            ),
            # The label is text and is quoted; the expression is code and is not.
            (
                lambda: toast.js.danger("Failed", action=("Retry", call("send"))),
                '$toast.danger("Failed", '
                '{ action: { label: "Retry", onClick: () => { send() } } })',
            ),
            # on_click takes statements, so an action has to as well: a bare
            # arrow body would make the whole call a syntax error.
            (
                lambda: toast.js.info(
                    "Archived", action=("Undo", unsafe("restored = true; save()"))
                ),
                '$toast.info("Archived", { action: { label: "Undo", '
                "onClick: () => { restored = true; save() } } })",
            ),
        ],
        ids=["bare", "variant", "description", "duration", "stays", "action", "body"],
    )
    def test_a_toast_is_written_with_its_options_quoted(self, call_, expected):
        assert call_() == expected

    def test_an_action_must_be_an_expression(self):
        # It is spliced into code, so a string from anywhere would run.
        with pytest.raises(TypeError):
            toast.js.danger("Could not send", action=("Retry", "send()"))  # type: ignore[arg-type]
