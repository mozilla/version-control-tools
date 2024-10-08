# -*- coding: utf-8 -*-
#
import datetime
import os
import sys

HERE = os.path.abspath(os.path.dirname(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(ROOT, "pylib", "mozautomation"))
sys.path.insert(0, os.path.join(ROOT, "pylib", "mozhg"))

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.graphviz",
    "sphinxcontrib.blockdiag",
    "sphinxcontrib.nwdiag",
    "sphinxcontrib.seqdiag",
]

templates_path = ["_templates"]

source_suffix = ".rst"

# source_encoding = 'utf-8-sig'

master_doc = "index"

project = "Mozilla Version Control Tools"

now = datetime.datetime.utcnow()
copyright = "%d, Mozilla" % now.year

version = "0"
release = "0"

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
# language = None

exclude_patterns = ["_build"]

pygments_style = "sphinx"

html_theme = "default"

html_static_path = ["_static"]

htmlhelp_basename = "MozillaVersionControlToolsdoc"

# Read The Docs can't import sphinx_rtd_theme, so don't import it there.
on_rtd = os.environ.get("READTHEDOCS", None) == "True"

if not on_rtd:
    import sphinx_rtd_theme

    html_theme = "sphinx_rtd_theme"
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
