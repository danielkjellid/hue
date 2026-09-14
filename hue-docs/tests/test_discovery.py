import pytest
from hue import ui
from hue.ui.base import ChainableComponent

from hue_docs.discovery import discover, documented_components
from hue_docs.registry import example_body, example_code


def _exported_components() -> dict[str, type[ChainableComponent]]:
    return {
        name: obj
        for name in ui.__all__
        if isinstance(obj := getattr(ui, name), type)
        and issubclass(obj, ChainableComponent)
        and obj is not ChainableComponent
    }


def test_discovers_every_component_unless_it_opts_out():
    discovered = {doc.name for doc in discover()}
    exported = _exported_components()

    assert discovered == set(documented_components())
    # The only way out of the docs is the explicit composition-only marker.
    skipped = set(exported) - discovered
    assert skipped == {name for name, cls in exported.items() if cls.category is None}
    assert "TableRow" in skipped


def test_documented_component_without_example_fails_loudly(monkeypatch):
    class Lonely(ChainableComponent):
        def _render(self, context):
            return ""

    monkeypatch.setattr(ui, "Lonely", Lonely, raising=False)
    monkeypatch.setattr(ui, "__all__", [*ui.__all__, "Lonely"])

    with pytest.raises(TypeError, match="defines no example"):
        discover()


@pytest.mark.parametrize("doc", discover(), ids=lambda d: d.name)
def test_example_is_a_single_expression(doc):
    # The docs show the body of example() verbatim as the usage snippet, so a
    # multi-statement body would leak undefined local names into the site.
    assert example_body(doc) is not None, f"{doc.name}.example() is not one return"
    code = example_code(doc)
    assert code is None or code.startswith(f"{doc.name}(")


@pytest.mark.parametrize("doc", discover(), ids=lambda d: d.name)
def test_axis_defaults_are_real_values(doc):
    for axis in doc.axes:
        if axis.default is None:
            continue
        if axis.kind == "bool":
            assert isinstance(axis.default, bool), (doc.name, axis.method)
        else:
            assert axis.default in axis.values, (doc.name, axis.method)


def test_button_variant_axis_is_introspected():
    button = next(doc for doc in discover() if doc.name == "Button")
    variant = next(axis for axis in button.axes if axis.method == "variant")

    assert variant.kind == "enum"
    assert "primary" in variant.values
    assert "danger-outline" in variant.values
    assert variant.default == "primary"


def test_constructor_defaults_override_render_defaults():
    email = next(doc for doc in discover() if doc.name == "EmailInput")
    autocomplete = next(axis for axis in email.axes if axis.method == "autocomplete")

    assert autocomplete.default == "email"


def test_bool_modifier_becomes_toggle_axis():
    text = next(doc for doc in discover() if doc.name == "Text")
    muted = next(axis for axis in text.axes if axis.method == "muted")

    assert muted.kind == "bool"
    assert muted.values == [False, True]
    assert muted.default is False


def test_shared_base_modifiers_are_not_axes():
    button = next(doc for doc in discover() if doc.name == "Button")
    axis_methods = {axis.method for axis in button.axes}

    assert "class_" not in axis_methods
    assert "content" not in axis_methods


@pytest.mark.parametrize("doc", discover(), ids=lambda d: d.name)
def test_components_carry_a_prose_description(doc):
    assert doc.paragraphs, f"{doc.name} has no description paragraphs"
    for paragraph in doc.paragraphs:
        # Indented code samples in docstrings must not leak into the prose.
        assert "().name(" not in paragraph and "create_icon_base(" not in paragraph
