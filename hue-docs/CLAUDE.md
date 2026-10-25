# hue-docs: writing the documentation

Two sites live in this package until the rename. `src/hue_docs/` is v1, the static
generator that discovers components through `example()`. Leave it alone: it keeps
working until v2 replaces it. `src/hue_docs_v2/` is the new site, and everything
below is about v2.

## How v2 is built

- A FastAPI app (`app.py`) renders every page. `make serve-v2` runs it live on
  port 8001.
- `make build-v2` freezes every page and frame to `dist-v2/` with the app's own
  TestClient, highlights code with Shiki, builds Tailwind and indexes the pages with
  Pagefind.
- Cloudflare serves `dist-v2/` as static assets. A Python Worker (`worker/`) runs only
  the routes under `/demos/`, which are the live demos. `make preview-v2` runs both
  locally the way Cloudflare does.

## Pages are declared, not discovered

Every page is a module under `pages/`. A guide declares a `GuidePage` and is listed
in `pages/guides/__init__.py`. A component page declares a `ComponentPage` and is
listed in `pages/components/__init__.py`. Read `pages/components/button.py` first; it
is the template.

A component page names its class. The title, category, import line and props table
come from the class itself, so none of them is written by hand. What you write:

| Field | What goes in it |
| --- | --- |
| `lede` | Two or three sentences: what the component is and when it is the right one. |
| `panels` | The specimens. See the panel list below. |
| `usage` | The walkthrough: the API in use, how it fits with forms or routes, and the gotchas. |
| `notes` | Accessibility rows (`a11y`), plain facts (`note`) and traps (`warn`). |
| `parts` | Composition parts with no page of their own; they get a props table here. |
| `related` | Components a reader would compare this one with. |
| `views` | A `HueFragmentsView` for a demo that needs the server. |

### Examples

An example is a module-level function that returns one component in a single
`return`:

```python
def danger() -> Button:
    return Button().variant("danger").content("Delete")
```

The code shown beside the preview is that return expression, read from the source, so
it cannot drift from what rendered. A test fails on a function with any other
statement in it. The function name becomes the cell's caption, so name it after what
the cell shows (`danger`, `icon_only`, `field_error`). Use `captions=False` on a panel
whose examples already label themselves. Give every form control in a frame its own
`name()`, because a frame with two controls of one name has two elements with one id.

Use `Icon` from `hue_docs_v2.icons`. It stands in for the icon set a reader binds with
`create_icon_base`, and the copied code says so.

### Panels

Add the panels that apply and skip the rest. Each is `panel(label, *examples)`:

| Label | Shows |
| --- | --- |
| Live | One example to hover, focus and press. Usually `layout="center"`. |
| Variants | Every value of `variant()`. |
| Sizes | Every value of `size()`. |
| Anatomy | The parts: label, icon, hint, action, and what each optional piece adds. |
| States | What code can set: disabled, readonly, required, loading, selected, current. |
| Loading | The skeleton or busy state, where the component has one. |
| Empty | What it shows with no data, where that differs from the default. |
| Error | The invalid state and its message. |
| Width or Layout | Behaviour that changes with the viewport. Say what changes in `hint`. |

Hover and focus are left to the Live panel. Freezing them would take hooks in hue's
CSS, and the docs never change hue to suit themselves.

Each panel renders in an iframe with its own width presets, drag handle and theme. An
overlay that opens from a small trigger needs `min_height` so it has room inside the
frame.

### Lessons from moving every component

- A usage heading and a panel with the same name get the same id, which the id test
  catches. Name usage headings after the component ("Sizes of a Badge") or the topic.
- A demo that needs a page, such as a declared DataTable or Tabs swapping a region,
  uses a `HueView` and returns a full `Page` from its routes. Alpine AJAX takes out the
  target, and a reload of the URL the swap pushed still works.
- Inside a frame, `mod+k` belongs to the docs' search. Give a Command example another
  hotkey, such as "/", and show `mod+k` in the usage code only.
- Frames render without the docs' shortcut registry, so `CommandShortcuts()` and
  `MenuItem().shortcut()` go in usage code, not in an example.
- A popover inside a Dialog's body is clipped by the body's scroll. Put a nested
  overlay in the footer, or describe it in prose.
- Shared prose for a family of pages (the charts) goes in a module whose name starts
  with an underscore, such as `pages/components/_charts.py`, and is not registered.
- Specimen links can point anywhere: a frame ignores clicks on links outside
  `/demos/` and the page's own anchors.

## Writing rules

These apply to every sentence in `lede`, `usage`, `notes` and the guides.

1. Never invent behaviour. Check every claim against the component's code before
   you write it. If the code does not settle a question, leave the claim out and say so
   in the PR. An example: a horizontal `TextInput` keeps its 180px label column at every
   width. A hint saying the label moves above on narrow screens would have been a guess.
2. Each H2 section stands on its own. Search lands readers in the middle of a page,
   so name the component in the section instead of writing "it". Use H2 and H3 only.
3. Lists follow their content. Number steps that happen in order. Use bullets for
   everything else. Use a table to compare things.
4. Be direct. Write "Set `type("submit")`", not "You might want to consider setting
   the type". State facts plainly and drop the hedges the code does not need.
5. Link with the name of the target. Never write "click here".
6. Every code block names its language. `pr.code()` defaults to Python. Pass
   `language=` for anything else.
7. No em dashes (organisation rule). Use a comma, a colon, parentheses or two
   sentences.
8. Run the `humanizer:humanizer` skill on new or changed prose before you commit it.
9. Put every code name in backticks: a class, a function, a modifier such as
   `on_click()`, a parameter, an attribute, a header, a path or a value someone
   would type. `pr.p`, `pr.lead`, `pr.bullets` and notes render a backticked run as
   inline code. Inside an `Alert`, pass `pr.rich("...")` rather than `pr.p`, whose
   muted colour would override the alert's own.
10. Say the point instead of staging it behind a colon. A heading such as "Known on
    the server, outside the address: the body" becomes "Parameters in the body", and
    a sentence that sets up a reveal ("the reason is simple: ...") states the reason.
11. Stay framework agnostic. Hue's core knows no framework, and `hue-django` and
    `hue-fastapi` are two integrations of it. Where a detail differs (the CSRF field,
    a setting, how a view is mounted), name what it is in each, or keep the sentence
    general. Never write as if Django were the only one.
12. An example that posts to a route builds the route's own body type,
    `ajax(..., body=Archive(reason="duplicate"))`, rather than a dict shaped like it.

Facts about the code belong in the docs: why `icon_only()` takes a label, what
`loading()` does to the accessible name. Opinions about how readers should design their
UI do not.

## Checks

- `make lint` and `make test` from `hue-docs/`. The v2 suite is in `tests/v2/`. It
  renders every page and frame, checks ids, checks that every class exists in the built
  stylesheet, and freezes and indexes the whole site.
- Anything with keyboard, focus or overlay behaviour also gets a run in a real browser
  (see the root CLAUDE.md).
