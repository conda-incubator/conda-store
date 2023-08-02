project = 'conda-store'
copyright = '2022, Quansight'
author = 'Quansight'
release = '0.4.15'

extensions = [
    'myst_parser',
    'sphinx_panels',
    'sphinx_copybutton'
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = "pydata_sphinx_theme"
html_static_path = ['_static']
html_css_files = ['css/custom.css']
html_logo = "_static/images/conda-store-logo-symbol.svg"
html_theme_options = {
    "logo": {
        "text": "conda-store",
    },
    "show_prev_next": True,
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/conda-incubator/conda-store",
            "icon": "fa-brands fa-github",
        }
   ],
}
html_sidebars = {
  "**": [],
}

# MyST-parser configurations

myst_heading_anchors = 3
myst_enable_extensions = ["colon_fence"]
