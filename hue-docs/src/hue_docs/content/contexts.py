from __future__ import annotations

from hue.types.core import ComponentType

from hue_docs.content import _prose as pr
from hue_docs.models import ProsePage

_PROBLEM = '''class Nav(ChainableComponent):
    """A bit of navigation, assembled somewhere else."""

    def _render(self, context):
        return SidebarSection().content(
            SidebarItem().href("/").content("Home"),
            SidebarItem().href("/events").content("Events"),
        )


Sidebar().current("/events").content(SidebarBody().content(Nav()))'''

_CONTRACT = """@dataclass(frozen=True, slots=True)
class CurrentPage:
    path: str | None

    @classmethod
    def from_context(cls, context: Context) -> CurrentPage:
        found = context.get(cls)
        return found if isinstance(found, cls) else cls(None)


class Sidebar(ChainableComponent):
    def htmy_context(self) -> Context:
        return {CurrentPage: CurrentPage(self._get_prop("current"))}


class SidebarItem(Clickable):
    def _render(self, context: Context) -> Component:
        here = CurrentPage.from_context(context).path
        current = self._get_prop("current", href is not None and href == here)"""

_ANSWERS = """# A tab outside a row is a mistake. Say so.
@classmethod
def from_context(cls, context: Context) -> TabsState:
    found = context.get(cls)
    if isinstance(found, cls):
        return found
    raise ValueError(
        "A Tab, TabList or TabPanel only means something inside Tabs, "
        "which is what says which of them is showing."
    )


# A control outside a form is ordinary. Answer with nothing wrong.
@classmethod
def from_context(cls, context: Context) -> FormErrors:
    found = context.get(cls)
    return found if isinstance(found, cls) else cls()"""

_NESTING = """Tabs().variant("underline").content(
    TabPanel().content(
        # A row inside a panel. Everything in here reads "segmented";
        # everything outside it still reads "underline".
        Tabs().variant("segmented").content(...),
    ),
)"""


def _build() -> ComponentType:
    return pr.page(
        pr.h1("Contexts"),
        pr.lead(
            "A component can offer a value to everything rendered inside it, "
            "and a component anywhere in that subtree can ask for it by type. "
            "It is how a sidebar tells its links which page they are on, a "
            "form tells its controls what is wrong with them, and a row of "
            "tabs tells a panel whether it is showing."
        ),
        pr.h2("What a prop cannot do"),
        pr.p(
            "A component holds the children it was given, so anything it "
            "needs to tell them can be set on them when they are built. That "
            "works right up to the point where it is not the one building "
            "them."
        ),
        pr.code(_PROBLEM),
        pr.p(
            "The sidebar's children are one SidebarBody holding one Nav. The "
            "items do not exist yet, and when they do it is Nav that makes "
            "them, which knows nothing about the current page. A prop cannot "
            "cross that, and neither can a walk over the tree: the children "
            "of a component are what was attached to it, not what it will "
            "eventually render."
        ),
        pr.p(
            "A context goes the other way. Instead of the sidebar reaching "
            "down to mark an item, it offers the path, and each item marks "
            "itself as it renders."
        ),
        pr.h2("The contract"),
        pr.p(
            "Two halves, and neither of them is a base class. A component "
            "that offers something defines htmy_context() and returns a "
            "mapping. A component that wants something reads it off the "
            "context its _render is handed. Anything between the two can be "
            "any depth of anything."
        ),
        pr.code(_CONTRACT),
        pr.p(
            "The key is the class itself and the value an instance of it, so "
            "a lookup is a type and there is nothing to spell wrong. Keep "
            "the value frozen: it is read by everything inside and owned by "
            "none of them, and a mutable one turns render order into "
            "behaviour."
        ),
        pr.p(
            "from_context() as a classmethod on the key is a convention "
            "rather than a requirement, but it is worth keeping. It is the "
            "one place that knows what the key is, what the value looks like "
            "and what to do when nobody offered one, so every reader is a "
            "single call that either answers or explains itself."
        ),
        pr.h2("Answer, or raise"),
        pr.p(
            "What a missing provider means is the component's own decision, "
            "and both answers are right somewhere. Raise when the component "
            "is meaningless without it; default when its absence is an "
            "ordinary way to use it."
        ),
        pr.code(_ANSWERS),
        pr.h2("The nearest provider wins"),
        pr.p(
            "Contexts nest. htmy chains each provider's mapping in front of "
            "the one it inherited, so a provider inside a provider shadows it "
            "for its own subtree and leaves the rest alone. A provider also "
            "sees its own context, which is what lets a component offer a "
            "value and read it in the same _render."
        ),
        pr.code(_NESTING),
        pr.h2("What hue already offers"),
        pr.bullets(
            [
                pr.p(
                    "HueContext - the request and the CSRF token, put there "
                    "by render_tree. Every component looks it up and throws "
                    "it away, so a tree rendered outside one fails at the "
                    "first component rather than at whichever one later "
                    "wants a token."
                ),
                pr.p(
                    "CurrentPage - the path Sidebar was told it is on. A "
                    "SidebarItem whose href matches marks itself."
                ),
                pr.p(
                    "TabsState - how a row of tabs is drawn. TabList, Tab "
                    "and TabPanel all read it, and all three raise without "
                    "it."
                ),
                pr.p(
                    "FormErrors - what came back wrong, by control name. "
                    "Every named control looks itself up; one given an error "
                    "explicitly keeps it, so the form is the fallback rather "
                    "than an override."
                ),
            ]
        ),
        pr.h2("When not to reach for one"),
        pr.p(
            "Hue is declarative on purpose: a call site should say what it "
            "renders. A context is the opposite of that, because what a "
            "component does now depends on something written somewhere else. "
            "That is a real cost, and it is only worth paying where a prop "
            "genuinely cannot reach."
        ),
        pr.p(
            "The request is the case to avoid. It is already in the context "
            "and almost nothing reads it, which is the healthy outcome: a "
            "leaf component that reaches for the request is one you can no "
            "longer render without building one."
        ),
    )


PAGE = ProsePage(
    slug="contexts",
    title="Contexts",
    nav_label="Contexts",
    group="Guides",
    order=3,
    build=_build,
)
