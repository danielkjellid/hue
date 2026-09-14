import pytest

from hue.utils import classnames


@pytest.mark.parametrize(
    "classes, expected_str",
    (
        # Basic string arguments
        (("foo",), "foo"),
        (("foo", "bar"), "foo bar"),
        (("foo", "bar", "baz"), "foo bar baz"),
        # List arguments
        ((["foo", "bar"],), "foo bar"),
        ((["foo", "bar"], "baz"), "foo bar baz"),
        (("foo", ["bar", "baz"]), "foo bar baz"),
        # Dict arguments
        (({"foo": True, "bar": False},), "foo"),
        (({"foo": True, "bar": True},), "foo bar"),
        (({"foo": False, "bar": False},), ""),
        # None values (should be ignored)
        (("foo", None, "bar"), "foo bar"),
        ((None, "foo"), "foo"),
        (("foo", None), "foo"),
        ((None,), ""),
        # Empty strings (should be ignored)
        (("foo", "", "bar"), "foo bar"),
        ((["foo", "", "bar"],), "foo bar"),
        (("",), ""),
        # Combinations
        (("foo", {"bar": True, "baz": False}), "foo bar"),
        (("foo", None, ["bar", "baz"]), "foo bar baz"),
        ((["foo", "bar"], {"baz": True, "qux": False}), "foo bar baz"),
        (("foo", None, ["bar"], {"baz": True}), "foo bar baz"),
        # Real-world examples from text.py
        # Text component with muted and not destructive
        (
            (
                {
                    "text-surface-500": True,
                    "text-destructive": False,
                    "text-surface-900": False,
                },
            ),
            "text-surface-500",
        ),
        # Text component with destructive
        (
            (
                {
                    "text-surface-500": False,
                    "text-destructive": True,
                    "text-surface-900": False,
                },
            ),
            "text-destructive",
        ),
        # Text component with normal (not muted, not destructive)
        (
            (
                {
                    "text-surface-500": False,
                    "text-destructive": False,
                    "text-surface-900": True,
                },
            ),
            "text-surface-900",
        ),
        # Label component example
        (
            (
                {
                    "pointer-events-none text-surface-300": False,
                    "cursor-pointer": True,
                    "sr-only": False,
                },
                "inline-flex items-center gap-1 text-surface-900",
            ),
            "cursor-pointer inline-flex items-center gap-1 text-surface-900",
        ),
        # BaseText component example with variant and align
        (
            (
                {
                    "text-5xl font-bold": True,
                    "text-3xl font-bold": False,
                    "text-2xl": False,
                    "text-base font-medium": False,
                    "text-sm font-medium leading-6": False,
                    "text-sm leading-6": False,
                },
                {"text-center": False, "text-right": False, "text-left": True},
                "custom-class",
            ),
            "text-5xl font-bold text-left custom-class",
        ),
        # Edge cases
        ((), ""),
        (("foo", [], {"bar": False}), "foo"),
        ((["foo", "bar"], None, {"baz": True}, "qux"), "foo bar baz qux"),
    ),
)
def test_classnames(classes, expected_str):
    assert classnames(*classes) == expected_str
