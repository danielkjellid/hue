class AJAXRequiredError(Exception):
    """Exception raised when an AJAX request is required but not provided."""

    def __init__(self) -> None:
        self.message = "AJAX request required"
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message


class BodyValidationError(Exception):
    """
    Exception raised when request body validation fails.

    Contains structured error information from Pydantic validation.
    """

    def __init__(self, errors: list[dict]) -> None:
        self.errors = errors
        self.message = "Request body validation failed"
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"{self.message}: {self.errors}"
