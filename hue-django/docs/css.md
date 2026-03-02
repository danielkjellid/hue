## CSS

Hue serves its own pre-built CSS automatically via a Django middleware. No `collectstatic` or static file configuration needed for Hue's component styles.

### Setup

Add the middleware to your `MIDDLEWARE` setting:

```python
# settings.py

MIDDLEWARE = [
    "hue_django.middleware.HueAssetsMiddleware",
    # ... your other middleware
]
```

That's it. Hue's CSS is now served at `/__hue__/styles.css` and its JavaScript at `/__hue__/js/alpine.js`, directly from the Python package.

### Adding your own CSS

If you need custom styles (color overrides, extra CSS rules, or your own Tailwind build), build and serve your CSS however you like, then tell Hue about it via the `HUE_EXTRA_CSS_URLS` setting:

```python
# settings.py

HUE_EXTRA_CSS_URLS = ["/static/my-overrides.css"]
```

Hue includes these as additional `<link>` tags in the `<head>`, after its own CSS. This means your styles take precedence over Hue's defaults.

### Example — Overriding colors

Create a plain CSS file (no build pipeline needed):

```css
/* static/my-overrides.css */
:root {
  --color-primary-500: #8B5CF6;
  --color-primary-600: #7C3AED;
}

.my-custom-component {
  padding: 1rem;
}
```

Serve it via Django's `staticfiles` and add it to the setting:

```python
# settings.py

STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
HUE_EXTRA_CSS_URLS = ["/static/my-overrides.css"]
```

### Example — Using Tailwind for your own code

If you want to use Tailwind utility classes in **your** code (not Hue components), set up your own Tailwind build. Hue's CSS handles Hue components; your CSS handles your code.

```css
/* static/tailwind.input.css */
@import "tailwindcss";

/* Your custom styles — Tailwind will compile utility classes from your code */
```

Build it however you prefer (`pytailwindcss`, `npx tailwindcss`, etc.), then serve the output and add it:

```python
# settings.py

HUE_EXTRA_CSS_URLS = ["/static/my-tailwind.css"]
```

### Advanced — Accessing Hue's CSS source

For deep customization (e.g., importing Hue's theme variables into your own Tailwind build), the source CSS path is available via `hue.assets`:

```python
from hue.assets import css_source_path

print(css_source_path())
# /path/to/site-packages/hue/static/styles/tailwind.input.css
```
