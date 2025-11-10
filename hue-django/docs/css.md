## CSS

Hue comes pre-built with bundled CSS that you can use without any additional configuration. This gives you flexibility if you just want to sprinkle some of Hue inside your existing UI.

However, in most realistic cases you'll probably end up overwriting the base CSS colors and classes to fit your needs. In addition, if you have `htmy` as a dependency, you might end up writing custom CSS to encapsulate Hue components.

To achieve this while still keeping Hue working, you need to extend the built CSS file and bundle it yourself. Once that's done, you need to tell Hue how to locate your bundled CSS file.

### Extending the CSS file

To extend the CSS file, simply reference the pre-built CSS file through the `@import` directive.

```css
/* my.css */
@import url("<STATIC_ROOT>/hue/styles/tailwind.css");

.my-custom-css {
  color: red;
}
```

How you build or minify your own CSS is completely up to you, but the built file needs to be picked up when running `python manage.py collectstatic`.

Once the file is built, set the path relative to your `STATIC_ROOT` in the `HUE_CSS_STATIC_PATH` setting:

```python
# settings.py

HUE_CSS_STATIC_PATH = "styles/my.css"
```

### Tailwind example

Here's a complete example using Tailwind CSS:

```python
# myproject/settings.py

STATIC_ROOT = BASE_DIR / "www" / "static"
STATICFILES_DIRS = [os.path.join(APP_DIR, "static")]
```

```css
/* myproject/static/tailwind.input.css */
@import "tailwindcss";
@import "../../../www/static/hue/styles/tailwind.css";
```

```python
# myproject/myapp/views.py

from hue import ui
from hue_django.views import HueView
from htmy import html, Context

class MyView(HueView):
  title = "My view"

  def body(self, context: Context) -> html.div:
    return html.div(
      ui.Button("Hello"),
      class_="max-w-md"  # Not part of Hue's CSS, but will be included in the built file.
    )
```

Using `pytailwindcss` (`tailwindcss -i myproject/static/tailwind.input.css -o myproject/static/styles/tailwind.css`) will detect the Tailwind classes across the codebase and use the input file as a reference point when building the CSS file. For example, it will include all pre-built Hue CSS, as well as the `max-w-md` class used in the views file.

Once that is done, point the `HUE_CSS_STATIC_PATH` setting to the path relative to your static root. E.g. `HUE_CSS_STATIC_PATH = "styles/tailwind.css"` in this case.
