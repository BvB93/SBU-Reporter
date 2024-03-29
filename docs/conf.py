# -*- coding: utf-8 -*-
#
# sbu documentation build configuration file, created by
# sphinx-quickstart on Thu May 30 13:59:47 2019.
#
# This file is execfile()d with the current directory set to its
# containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

import os
import sys

import sbu

here = os.path.dirname(__file__)
sys.path.insert(0, os.path.abspath(os.path.join(here, '..')))


# -- General configuration ------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx_autodoc_typehints',
    'sphinx.ext.intersphinx',
    'sphinx.ext.viewcode',
    'sphinx.ext.autosummary',
    'matplotlib.sphinxext.plot_directive'
]


# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']


# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
# source_suffix = ['.rst', '.md']
source_suffix = '.rst'


# The master toctree document.
master_doc = 'index'


# General information about the project.
project = 'SBU-Reporter'
copyright = '2021, Bas van Beek'
author = "Bas van Beek"


# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
version = sbu.__version__.rsplit('.', 1)[0]  # The short X.Y version.
release = sbu.__version__   # The full version, including alpha/beta/rc tags.


# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = 'en'


# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'


# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = False


# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = 'sphinx_rtd_theme'


# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
# html_theme_options = {}


# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
html_context = {'css_files': [
    '_static/theme_overrides.css',  # override wide tables in RTD theme
]}


# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
#
# This is required for the alabaster theme
# refs: http://alabaster.readthedocs.io/en/latest/installation.html#sidebars
html_sidebars = {'**': [
    'relations.html',  # needs 'show_related': True theme option to display
    'searchbox.html',
]}


# -- Options for HTMLHelp output ------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = 'sbu_doc'


# -- Options for LaTeX output ---------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',

    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',

    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',

    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [(
    master_doc,
    'sbu.tex',
    u'SBU-Reporter Documentation',
    u"B. F. van Beek",
    'manual'
)]


# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [(
    master_doc,
    'sbu',
    u'SBU-Reporter Documentation',
    [author],
    1
)]


# -- Options for Texinfo output -------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [(
    master_doc,
    'sbu',
    u'SBU-Reporter Documentation',
    author,
    'sbu',
    'Tools for collection, formating and reporting SBU usage on the SURFsara HPC clusters.',
    'Miscellaneous'
)]


# Whether to show links to the files in HTML.
plot_html_show_formats = False


# Whether to show a link to the source in HTML.
plot_html_show_source_link = False


# File formats to generate. List of tuples or strings:
plot_formats = [('png', 300)]


# This value selects if automatically documented members are sorted alphabetical (value 'alphabetical'), by member type (value 'groupwise') or by source order (value 'bysource').
autodoc_member_order = 'bysource'


# This value controls the behavior of sphinx-build -W during importing modules.
autodoc_warningiserror = True


# True to parse Google style docstrings.
# False to disable support for Google style docstrings.
# Defaults to True.
napoleon_google_docstring = True


# True to parse NumPy style docstrings.
# False to disable support for NumPy style docstrings.
# Defaults to True.
napoleon_numpy_docstring = True


# True to use the .. admonition:: directive for the Example and Examples sections.
# False to use the .. rubric:: directive instead. One may look better than the other depending on what HTML theme is used.
# Defaults to False.
napoleon_use_admonition_for_examples = True

# True to use the :ivar: role for instance variables.
# False to use the .. attribute:: directive instead.
#  Defaults to False.
napoleon_use_ivar = True


# True to include private members (like _membername) with docstrings in the documentation.
# False to fall back to Sphinx’s default behavior.
# Defaults to False.
napoleon_include_private_with_doc = False


# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {
    'python': ('https://docs.python.org/', None),
    'pandas': ('https://pandas.pydata.org/pandas-docs/stable/', None),
    'matplotlib': ('http://matplotlib.org', None),
    'seaborn':  ('https://seaborn.pydata.org/', None)
}
