"""
The app for make serve: live pages, with the build's assets beneath them.
"""

from fastapi import FastAPI

from hue_docs.app import create_app
from hue_docs.freeze import DIST


def app() -> FastAPI:
    return create_app(static_dir=DIST)
