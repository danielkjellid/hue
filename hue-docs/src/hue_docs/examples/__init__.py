"""Optional, hand-authored showcases for individual components.

Each module exports either ``EXAMPLE`` + ``COMPONENT`` (a single component) or
``EXAMPLES`` (a ``{class_name: ComponentExample}`` mapping). Modules are
auto-discovered by :func:`hue_docs.registry.load_examples`, so adding a richer
demo is just adding a file here — no navigation to update.
"""
