# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import sys
import os

# The 2nd parent dir of this current dir is the root dir
cwd = os.getcwd()
# going two dirs back to reach the root dir
project_root = os.path.dirname(os.path.dirname(cwd))

py_root = os.path.join(project_root, "telegrambot")

# Add the root dir to the system path
sys.path.insert(0, py_root)
sys.path.insert(0, project_root)

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "A simple telegram bot"
copyright = "2023, Farhad Sabrian"
author = "Farhad Sabrian"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx.ext.autodoc", "sphinx.ext.viewcode"]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# The suffix of source filenames.
source_suffix = ".rst"

# The master toctree document.
master_doc = "index"

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme = "default"
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
