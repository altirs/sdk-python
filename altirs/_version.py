"""Single source of truth for the version: the installed package metadata."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("altirs-sdk")
except PackageNotFoundError:  # running from a source checkout
    __version__ = "0.0.0.dev0"
