from typing import Literal

type AriaRole = (
    Literal[
        # Widget roles
        "alert",
        "alertdialog",
        "button",
        "checkbox",
        "dialog",
        "gridcell",
        "link",
        "log",
        "marquee",
        "menuitem",
        "menuitemcheckbox",
        "menuitemradio",
        "option",
        "progressbar",
        "radio",
        "scrollbar",
        "searchbox",
        "separator",
        "slider",
        "spinbutton",
        "status",
        "switch",
        "tab",
        "tabpanel",
        "textbox",
        "timer",
        "tooltip",
        "treeitem",
        # Composite roles
        "combobox",
        "grid",
        "listbox",
        "menu",
        "menubar",
        "radiogroup",
        "tablist",
        "tree",
        "treegrid",
        # Document structure roles
        "article",
        "cell",
        "columnheader",
        "definition",
        "directory",
        "document",
        "feed",
        "figure",
        "group",
        "heading",
        "img",
        "list",
        "listitem",
        "math",
        "none",
        "note",
        "presentation",
        "row",
        "rowgroup",
        "rowheader",
        "table",
        "term",
        "toolbar",
        # Landmark roles
        "banner",
        "complementary",
        "contentinfo",
        "form",
        "main",
        "navigation",
        "region",
        "search",
    ]
    | None
)

type AriaHasPopup = (
    Literal["menu", "listbox", "tree", "grid", "dialog", "true", "false"] | None
)
type AriaAtomic = Literal["true", "false"] | None
type AriaLive = Literal["off", "polite", "assertive"] | None
