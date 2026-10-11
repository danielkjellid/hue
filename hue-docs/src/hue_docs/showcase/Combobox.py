"""
Curated showcases for the Combobox molecule.

The auto-grid has the sizes and the multiple flag over four options, which is
too short a list to need searching. These have enough options to filter, and
show the groups, the tokens, the empty message and a bound value.
"""

from __future__ import annotations

import textwrap

from hue_docs.showcase import Showcase, variant


def _at(block: str, depth: int) -> str:
    """
    A shared block of source indented to sit at depth in a snippet, so the
    code shown on the page lines up wherever the block is dropped in.
    """
    return textwrap.indent(textwrap.dedent(block).strip(), " " * depth).lstrip()


_NORDICS = """
    SelectGroup().label("Nordics").content(
        SelectOption().value("no").label("Norway").meta("NO"),
        SelectOption().value("se").label("Sweden").meta("SE"),
        SelectOption().value("dk").label("Denmark").meta("DK"),
        SelectOption().value("fi").label("Finland").meta("FI"),
        SelectOption().value("is").label("Iceland").meta("IS"),
    )
"""

_EUROPE = """
    SelectGroup().label("Rest of Europe").content(
        SelectOption().value("de").label("Germany").meta("DE"),
        SelectOption().value("nl").label("Netherlands").meta("NL"),
        SelectOption().value("fr").label("France").meta("FR"),
        SelectOption().value("gb").label("United Kingdom").meta("GB"),
        SelectOption().value("ie").label("Ireland").meta("IE"),
    )
"""

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            "Type in any of these to filter the list: an option stays when its "
            "label contains what was typed, and a group goes once nothing in it "
            "is left. The arrow keys move through what remains and Enter picks."
        ),
        variants=[
            variant(
                "Grouped, with a value",
                f"""
                (
                    Combobox().name("country")
                    .label("Country")
                    .placeholder("Search countries")
                    .value("se")
                    .hint("Where the invoice is sent from.")
                    .content(
                        {_at(_NORDICS, 24)},
                        {_at(_EUROPE, 24)},
                    )
                )
                """,
            ),
            variant(
                "Several values",
                f"""
                (
                    Combobox().name("markets")
                    .label("Markets")
                    .placeholder("Add another…")
                    .multiple()
                    .value("no", "se", "dk")
                    .content(
                        {_at(_NORDICS, 24)},
                        {_at(_EUROPE, 24)},
                    )
                )
                """,
            ),
            variant(
                "Options with more to say",
                """
                (
                    Combobox().name("assignee")
                    .label("Assignee")
                    .placeholder("Search people")
                    .content(
                        SelectOption().value("ada").label("Ada Lovelace")
                            .description("Engineering"),
                        SelectOption().value("grace").label("Grace Hopper")
                            .description("Platform"),
                        SelectOption().value("alan").label("Alan Turing")
                            .description("Research · on leave").disabled(),
                        SelectOption().value("edsger").label("Edsger Dijkstra")
                            .description("Engineering"),
                    )
                )
                """,
            ),
            variant(
                "Its own empty message",
                f"""
                (
                    Combobox().name("ship_to")
                    .label("Ship to")
                    .placeholder("Try typing Japan")
                    .empty_message("We do not ship there yet.")
                    .content({_at(_NORDICS, 20)})
                )
                """,
            ),
            variant(
                "Invalid",
                f"""
                (
                    Combobox().name("billing_country")
                    .label("Billing country")
                    .placeholder("Search countries")
                    .required()
                    .error("Pick the country the card is registered in.")
                    .content({_at(_NORDICS, 20)})
                )
                """,
            ),
        ],
    ),
    Showcase(
        title="Binding the value",
        layout="stack",
        description=(
            "x_model binds what is chosen, never what is typed: the value for a "
            "single combobox, and the list of values for a multiple one. Both "
            "directions work, so Alpine data can set the choice as well as read "
            "it."
        ),
        variants=[
            variant(
                "Read back as you choose",
                f"""
                (
                    Stack().x_data({{"markets": ["no"]}}).content(
                        Combobox().name("bound_markets")
                        .label("Markets")
                        .multiple()
                        .x_model(unsafe("markets"))
                        .content({_at(_NORDICS, 24)}),
                        Text().x_text(unsafe("'Chosen: ' + markets.join(', ')")),
                    )
                )
                """,
            ),
        ],
    ),
]
