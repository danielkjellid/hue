"""
The Worker's entry point: the docs' demo routes on Cloudflare's ASGI adapter.
"""

from workers import asgi

from hue_docs.app import demo_app

Default = asgi.entrypoint(demo_app())
