import pytest
from django.test import RequestFactory, override_settings
from hue import shortcuts
from hue.js import unsafe
from hue.shortcuts import Shortcut, ShortcutRegistry

from hue_django.middleware import HueRequestMiddleware
from hue_django.router import Router


class Shortcuts(ShortcutRegistry):
    home = Shortcut("Home", "g", "h", href="/")
    archive = Shortcut("Archive", "e", scoped=True)


def _registry():
    return Router()._get_context_args(RequestFactory().get("/"))["shortcuts"]


def test_an_app_has_no_shortcuts_until_a_setting_names_them():
    assert _registry() is None


@override_settings(HUE_SHORTCUTS="tests.test_shortcuts.Shortcuts")
def test_the_setting_reaches_every_render_as_a_path():
    assert _registry() is Shortcuts


@override_settings(HUE_SHORTCUTS=Shortcuts)
def test_the_setting_can_be_the_class_itself():
    assert _registry() is Shortcuts


@override_settings(HUE_SHORTCUTS="tests.test_shortcuts.Router")
def test_a_setting_that_is_not_a_registry_is_refused():
    with pytest.raises(TypeError):
        _registry()


def test_a_plain_view_can_switch_on_a_scoped_shortcut():
    # The middleware opens the list the way it opens the toast queue.
    used = []

    def view(request):
        shortcuts.use(Shortcuts.archive, action=unsafe("archive()"))
        used.extend(shortcuts.used())
        return "ok"

    HueRequestMiddleware(view)(RequestFactory().get("/"))
    assert [item.shortcut for item in used] == [Shortcuts.archive]
