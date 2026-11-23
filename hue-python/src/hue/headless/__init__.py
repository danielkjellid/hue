"""
Hue's widgets as unstyled parts: the structure, the ARIA, the Alpine behaviour
and the form contract, with no classes of their own.

hue.ui styles these parts, so this package never imports hue.ui. The ruff.toml
beside this file enforces that, which keeps the parts free to move into a
distribution of their own.
"""
