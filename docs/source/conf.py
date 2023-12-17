# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# The 2nd parent dir of this current dir is the root dir
cwd = os.getcwd()
# going two dirs back to reach the root dir
project_root = os.path.dirname(os.path.dirname(cwd))

protestcrawler_root = os.path.join(project_root, "protestcrawler")
telegrambot_root = os.path.join(project_root, "telegrambot")
telegrambot_libs = os.path.join(project_root, "telegrambot", "libs")

# Add the root dir to the system path
sys.path.insert(0, project_root)
sys.path.insert(0, protestcrawler_root)
sys.path.insert(0, telegrambot_root)
sys.path.insert(0, telegrambot_libs)

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "A Telegram Bot For Protests in Berlin"
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
# set a favicon
html_favicon = "_static/favicon.ico"
