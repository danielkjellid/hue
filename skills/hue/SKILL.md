---
name: hue
description: Builds server-rendered interfaces in Python with Hue (the hue-ui package, imported as hue), and with hue-django or hue-fastapi. Covers picking and composing Hue's chainable components, writing markup with hue.html, forms and AJAX routes, styling with Hue's tokens, and testing what you built. Use whenever a project has hue-ui, hue-django or hue-fastapi installed, imports from hue, or the user mentions Hue components.
---

# Build with Hue

Hue is a component library for Python that renders HTML. Each component is a Python object configured through chained modifiers and rendered with htmy. Hue's own Tailwind stylesheet styles them, and Alpine.js with Alpine AJAX makes them interactive. `hue-django` and `hue-fastapi` add views, a router, CSRF handling and routes that serve the assets.

## Read the docs first

The docs for the installed version ship inside the package as Markdown. Find them with:

```bash
python -c "import hue, pathlib; print(pathlib.Path(hue.__file__).parent / 'docs')"
```

- Read `llms.txt` in that folder first. It lists every guide and component page with a one-line summary.
- Then read only the pages your task needs, like `components/select.md` or `forms.md`. Each component page has its import line, examples, a usage walkthrough, every modifier with its default, and accessibility notes.
- If `docs/` is missing, the installed version predates it. Read the component's class in the installed package instead. Its docstrings and modifier signatures are the API.
- The docs and the type hints are the contract. Don't infer behaviour from Hue's CSS or JavaScript bundles.

## Write the chain

A component is built by chaining modifiers. Each one returns the component:

```python
from hue.ui import Button, TextInput

TextInput().name("email").label("Email").required()
Button().variant("primary").type("submit").content("Save")
```

- Children go in `content(...)`.
- Set a control's name with `name()` rather than passing it to the constructor. `name()` sets the submitted name, the `id`, the label's `for` and the ids that the hint and error hang off.
- Boolean modifiers are named after the state they turn on and take no argument: `disabled()`, `required()`, `pill()`.
- Tone is always `variant()`, from `neutral`, `info`, `success`, `warning` and `danger`. A component offers only the tones it supports, so check its page.
- Size is always `size()`, from `xs`, `sm`, `md` and `lg`. Again, a component supports only some of these.

## Markup that isn't a component

Write plain elements with Hue's own `html` module. Its elements chain like components:

```python
from hue import html

html.a("Docs").href("/docs").class_("text-accent-text")
html.form(...).method("POST").action("/team/invite/").x_target("invite")
```

You never need to import htmy. Where a component takes an element, it takes the tag name, as in `Text().tag("h1")`.

Before you write an element with a `role`, check `llms.txt` for a Hue component that already does it. A hand-written `role="dialog"`, `"listbox"`, `"menu"`, `"tablist"`, `"switch"` or `"combobox"` next to Hue is almost always a bug: it lacks the keyboard handling, focus management and ARIA wiring that the Hue component has.

## Accessibility

- Every control needs an accessible name: `label()` on form controls, `icon_only("Delete")` on a button showing only an icon, `aria_label()` elsewhere. Components that need a name raise an error when it is missing. Don't silence that error with an empty string.
- Components already wire up their labels, hints, errors and ARIA state. Don't add `aria-*` attributes the component already sets.
- Use `sr-only` for text that should be read but not seen. Don't use `invisible` or `hidden`, which hide text from screen readers too.

## Forms and routes

Read `forms.md` and `actions.md` before you write a form or a route. The essentials:

- A named control submits its value under `name()`. `Select` submits through a hidden input, so a route reads it the same way as a `NativeSelect`.
- `Button` renders `type="button"` by default. The button that sends a form needs `type("submit")`.
- Disabled controls submit nothing and can't be reached with the keyboard.
- A route that answers AJAX requests is a `fragment_post` (or another fragment route) on the view's `Router`. A parameter named `body`, typed as a dataclass or a pydantic model, receives the validated fields. A body that fails validation answers 422. Override the view's `handle_body_validation_error` to render the errors back into the form instead.
- The response replaces the element whose id the form's `x-target` names. To show errors, return the form again with them.
- Stay framework agnostic in shared code. Only the view, the router import and the CSRF setup differ between `hue-django` and `hue-fastapi`.

## Alpine expressions

Never build an Alpine expression or an inline script by joining strings with text a user can change. Use `hue.js.call("fn", value)`, which quotes its arguments as JSON. Use `hue.js.unsafe(...)` only for fixed source code you wrote yourself.

## Styling

Hue's stylesheet covers Hue's components. Styling your own markup with Tailwind needs a Tailwind build of your own, served next to Hue's stylesheet (see `django/css.md` or `fastapi/setup.md`). Hue's token classes exist in that build only if it imports Hue's source stylesheet, whose path `hue.assets.css_source_path()` gives. In that build:

- Use the semantic token classes: `bg-surface`, `bg-canvas`, `text-fg`, `text-fg-muted`, `border-border`, `bg-accent`, `text-accent-text`, plus `success`, `warning`, `danger` and `info` with their `-subtle`, `-border` and `-text` steps. Hue defines no raw palette utilities like `bg-gray-500`.
- Don't add `dark:` variants for colour. The tokens switch with the theme.
- To change Hue's look, redefine a `--hue-*` ramp step or a semantic alias in your own stylesheet. Don't override the classes Hue's components use.

## Testing

- Render a component with `render_tree(component, context_args=HueContextArgs(request=..., csrf_token=...))` and parse the HTML. Assert on roles, names and attributes rather than on class names.
- Anything with keyboard, focus or overlay behaviour needs a test in a real browser (Playwright, for example) that presses real keys and checks where focus lands. Markup tests miss those bugs.

## When you're done

1. Run the project's type checker. Hue is fully typed, so a wrong modifier or variant name shows up there first.
2. Run the tests, including a browser check for anything interactive.
3. Report each command you ran and its result, anything you could not check, and anything the docs got wrong or left out.
