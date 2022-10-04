"""Sphinx configuration."""
project = "Obsidian Data"
author = "Josh Rickard"
copyright = "2022, Josh Rickard"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_click",
    "myst_parser",
]
autodoc_typehints = "description"
html_theme = "furo"
