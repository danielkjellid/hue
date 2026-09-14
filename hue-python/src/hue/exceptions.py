from typing import Any

from pydantic_core import ErrorDetails


class MissingHueContextError(Exception):
    """
    Raised when a hue component is rendered without a HueContext in scope.

    Every hue component needs a HueContext in its render context, much like a
    React component needs its context provider. render_tree and the framework
    integrations set this up; rendering through a bare htmy Renderer does not.
    """

    def __init__(self) -> None:
        self.message = (
            "Tried to render a hue component without a HueContext in scope.\n"
            "\n"
            "hue components must be rendered inside a hue render tree, which "
            "provides the context (request, csrf token, ...) to the whole tree, "
            "similar to a React context provider.\n"
            "\n"
            "Render through hue instead of a bare htmy Renderer, e.g.:\n"
            "\n"
            "    from hue.renderer import render_tree\n"
            "\n"
            "    html = await render_tree(component, context_args=context_args)\n"
            "\n"
            "(framework integrations such as hue-django do this for you)."
        )
        super().__init__(self.message)


class AJAXRequiredError(Exception):
    """
    Raised when a fragment route is requested without the AJAX headers.
    """

    def __init__(self) -> None:
        self.message = "AJAX request required"
        super().__init__(self.message)


class BodyValidationError(Exception):
    """
    Raised when request body validation fails.

    errors holds the structured error details from Pydantic.
    """

    def __init__(self, errors: list[dict[str, Any]] | list[ErrorDetails]) -> None:
        self.errors = errors
        self.message = "Request body validation failed"
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"{self.message}: {self.errors}"
