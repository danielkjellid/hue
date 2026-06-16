from typing import Callable

from hue.ui import EmailInput, NumberInput, PasswordInput, TextInput
from hue.ui.atoms.input import _BaseInput

from hue_docs.registry import ComponentExample, PlaygroundSpec, Showcase, Variant


def _play(ctor_code: str, build: Callable[[], _BaseInput]) -> PlaygroundSpec:
    return PlaygroundSpec(
        build=build,
        ctor_code=ctor_code,
        props=("required", "disabled", "hidden_label"),
    )


def _states(ctor_code: str, build: Callable[[], _BaseInput]) -> Showcase:
    return Showcase(
        title="States",
        layout="stack",
        variants=[
            Variant("default", build, ctor_code),
            Variant("required", lambda: build().required(), f"{ctor_code}.required()"),
            Variant("disabled", lambda: build().disabled(), f"{ctor_code}.disabled()"),
            Variant(
                "help text",
                lambda: build().help_text("We never share this."),
                f'{ctor_code}.help_text("We never share this.")',
            ),
            Variant(
                "error text",
                lambda: build().error_text("This field is required."),
                f'{ctor_code}.error_text("This field is required.")',
            ),
        ],
    )


def _text() -> TextInput:
    return (
        TextInput().name("username").label("Username").placeholder("Enter a username")
    )


def _email() -> EmailInput:
    return EmailInput().name("email").label("Email").placeholder("you@example.com")


def _password() -> PasswordInput:
    return PasswordInput().name("password").label("Password").placeholder("••••••••")


def _number() -> NumberInput:
    return NumberInput().name("quantity").label("Quantity").placeholder("0")


_TEXT_CTOR = 'TextInput().name("username").label("Username")'
_EMAIL_CTOR = 'EmailInput().name("email").label("Email")'
_PASSWORD_CTOR = 'PasswordInput().name("password").label("Password")'
_NUMBER_CTOR = 'NumberInput().name("quantity").label("Quantity")'

EXAMPLES = {
    "TextInput": ComponentExample(
        showcases=[_states(_TEXT_CTOR, _text)],
        playground=_play(_TEXT_CTOR, _text),
    ),
    "EmailInput": ComponentExample(
        showcases=[_states(_EMAIL_CTOR, _email)],
        playground=_play(_EMAIL_CTOR, _email),
    ),
    "PasswordInput": ComponentExample(
        showcases=[_states(_PASSWORD_CTOR, _password)],
        playground=_play(_PASSWORD_CTOR, _password),
    ),
    "NumberInput": ComponentExample(
        showcases=[
            _states(_NUMBER_CTOR, _number),
            Showcase(
                title="Constraints",
                layout="stack",
                variants=[
                    Variant(
                        "min / max / step",
                        lambda: _number().min(0).max(100).step(5),
                        f"{_NUMBER_CTOR}.min(0).max(100).step(5)",
                    ),
                ],
            ),
        ],
        playground=_play(_NUMBER_CTOR, _number),
    ),
}
