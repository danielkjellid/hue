from typing import Any

from arel import HotReload, Path
from htmy import html

# TODO: Make this configurable from settings.
hot_module_reload: Any = HotReload(
    paths=[
        Path("../views"),
        Path("../api"),
    ],
)


def hmr_script() -> html.script:
    """
    Load the arel hmr script, and inject it into the dom.
    """
    # The .script() method returns a string with the script tag, so we need to
    # extract the inner script and inject it into the dom through htmy.
    script = hot_module_reload.script(url="ws://localhost:8000/hmr")
    inner_script = script.split("<script>")[1].split("</script>")[0]

    return html.script(
        text=inner_script,
        type="text/javascript",
    )
