# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

# Configuration file for the Sphinx documentation builder.
import os
import sys

# Path setup - kritisch für Import-Erkennung
sys.path.insert(0, os.path.abspath(r'C:\Users\AC\PycharmProjects\Pattern_Pilot_v1.2'))

project = 'Holy Dashboard 3.1'
copyright = '2025, is-noname'
author = 'is-noname'
release = 'June 2025'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# Extensions - professionelle Ausstattung
extensions = [
    'sphinx.ext.autodoc',          # Automatische API-Docs
    'sphinx.ext.autosummary',      # Automatische Zusammenfassungen
    'sphinx.ext.viewcode',         # Source-Code-Links
    'sphinx.ext.napoleon',         # Google/NumPy Docstring-Stil
    'sphinx.ext.intersphinx',      # Cross-Referenzen
    'sphinx_autodoc_typehints',    # Type-Hint-Integration
    'sphinx.ext.todo',             # TO-DO-Listen
    'myst_parser',                 # Markdown-Support
]

# AutoDoc-Konfiguration - kritisch für Qualität
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

# Napoleon-Einstellungen für Trading-Dokumentation
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False

# HTML-Theme - Bloomberg-Style Terminal-Look
html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'collapse_navigation': False,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False,
    'style_external_links': True,
}

# HTML-Context für Trading-Spezifika
html_context = {
    'display_github': True,
    'github_user': 'dein-username',
    'github_repo': 'pattern-pilot',
    'github_version': 'main',
    'conf_py_path': '/docs/source/',
}

# Source-Suffixe
source_suffix = {
    '.rst': None,
    '.md': None,
}

# Autosummary-Generierung aktivieren
autosummary_generate = True

# Type-Hints-Konfiguration
typehints_fully_qualified = False
always_document_param_types = True

templates_path = ['_templates']
exclude_patterns = []

language = 'de'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
