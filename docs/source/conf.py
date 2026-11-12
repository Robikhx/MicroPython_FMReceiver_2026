import os
import sys

project = 'Micropico FM Receiver with Digital Tuning'
copyright = '2026, Robert Tarnita, Daniel Marchis, Comsa Danut'
author = 'Robert Tarnita, Daniel Marchis, Comsa Danut'

html_static_path = ['_static']

sys.path.insert(0, os.path.abspath('../../src'))

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',  # Generates summary tables for docstrings
    'sphinx.ext.napoleon',     # Google/NumPy docstring support
    'sphinx.ext.viewcode',     # Direct links to source code
    'myst_parser',             # Markdown support
    'sphinx_copybutton',       # Adds "Copy" buttons to code blocks
    'sphinx_rtd_theme',
]

html_theme_options = {
    'collapse_navigation': False,  # Keeps subheadings visible in the sidebar
    'sticky_navigation': True,     # Keeps sidebar fixed while scrolling
    'navigation_depth': 4,         # Controls how deep subheadings go (H1 to H4)
    'includehidden': True,         # Forces hidden toctrees into the main menu
    'titlesonly': False,           # Displays subheadings, not just page titles
}

autosummary_generate = True

html_theme = 'sphinx_rtd_theme'

myst_enable_extensions = [
    "colon_fence",
    "dollarmath",
    "html_image",
    "tables",
]

autodoc_mock_imports = [
    "machine",
    "micropython",
    "utime",
    "ujson",
]