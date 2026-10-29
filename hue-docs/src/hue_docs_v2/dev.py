"""
The app for make serve-v2: live pages, with the build's assets beneath them.
"""

from fastapi import FastAPI

from hue_docs_v2.app import create_app
from hue_docs_v2.freeze import DIST


def app() -> FastAPI:
    return create_app(static_dir=DIST)
