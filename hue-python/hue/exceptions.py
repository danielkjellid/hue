class AJAXRequiredError(Exception):
    """Exception raised when an AJAX request is required but not provided."""

    def __init__(self) -> None:
        self.message = "AJAX request required"
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message
