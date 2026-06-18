from hue import ui
from hue.ui.base import ChainableComponent

from hue_docs.discovery import discover


def _expected_component_names() -> set[str]:
    names = set()
    for name in ui.__all__:
        obj = getattr(ui, name)
        if (
            isinstance(obj, type)
            and issubclass(obj, ChainableComponent)
            and obj is not ChainableComponent
        ):
            names.add(name)
    return names


def test_discovers_every_component_in_ui_all():
    discovered = {doc.name for doc in discover()}
    assert discovered == _expected_component_names()


def test_button_variant_axis_is_introspected():
    button = next(doc for doc in discover() if doc.name == "Button")
    variant = next(axis for axis in button.axes if axis.method == "variant")

    assert variant.kind == "enum"
    assert "primary" in variant.values
    assert "outline-destructive" in variant.values
    assert variant.default == "primary"


def test_bool_modifier_becomes_toggle_axis():
    text = next(doc for doc in discover() if doc.name == "Text")
    muted = next(axis for axis in text.axes if axis.method == "muted")

    assert muted.kind == "bool"
    assert muted.values == [False, True]


def test_shared_base_modifiers_are_not_axes():
    button = next(doc for doc in discover() if doc.name == "Button")
    axis_methods = {axis.method for axis in button.axes}

    # class_/content/aria_* live on ChainableComponent and are not visual axes.
    assert "class_" not in axis_methods
    assert "content" not in axis_methods


def test_components_carry_a_description():
    for doc in discover():
        assert doc.paragraphs, f"{doc.name} has no description paragraphs"
