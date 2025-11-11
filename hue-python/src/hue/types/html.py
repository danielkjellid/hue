from typing import Literal

type AriaRole = (
    Literal[
        "button",
        "checkbox",
        "dialog",
        "gridcell",
        "link",
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
        "switch",
        "tab",
        "tabpanel",
        "textbox",
        "treeitem",
    ]
    | None
)

type AriaHasPopup = (
    Literal["menu", "listbox", "tree", "grid", "dialog", "true", "false"] | None
)
type AriaAtomic = Literal["true", "false"] | None
type AriaLive = Literal["off", "polite", "assertive"] | None
