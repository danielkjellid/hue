import pytest

from hue.ui import _shortcut


def test_a_chord_and_a_sequence_parse_to_their_keys():
    assert _shortcut.parse(("Mod+K",)) == (("mod", "k"),)
    assert _shortcut.parse(("g", "b")) == (("g",), ("b",))


@pytest.mark.parametrize(
    "steps",
    [(), ("mod",), ("mod+",), ("cmd+k",)],
    ids=["nothing", "a modifier alone", "no key", "an unknown modifier"],
)
def test_what_could_never_match_is_refused(steps):
    with pytest.raises(ValueError):
        _shortcut.parse(steps)
