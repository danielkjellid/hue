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

Facts about the code belong in the docs: why `icon_only()` takes a label, what
`loading()` does to the accessible name. Opinions about how readers should design their
UI do not.

## Checks

- `make lint` and `make test` from `hue-docs/`. The v2 suite is in `tests/v2/`. It
  renders every page and frame, checks ids, checks that every class exists in the built
  stylesheet, and freezes and indexes the whole site.
- Anything with keyboard, focus or overlay behaviour also gets a run in a real browser
  (see the root CLAUDE.md).
