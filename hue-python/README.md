# hue

A component library for Python that renders HTML. You build pages from Python
objects in a chainable style, and hue renders them with
[htmy](https://pypi.org/project/htmy/). The styling is Tailwind and the
interactivity is Alpine.js with Alpine AJAX. The stylesheet and scripts ship
inside the package, so there is no Node or Tailwind build step in your project.

```python
from hue.ui import Button, Stack, Text

Stack().horizontal().content(
    Text("Delete this project?"),
    Button().variant("danger").content(Text("Delete")),
)
```

## Install

The package is called `hue-ui`, and you import it as `hue`. Most projects
install a framework integration, which pulls in `hue-ui` and serves its assets:

```sh
uv add hue-django   # Django
uv add hue-fastapi  # FastAPI
```

All three packages release together under the same version number.

Source, docs and issues: https://github.com/danielkjellid/hue
