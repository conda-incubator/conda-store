import recommonmark
from recommonmark.transform import AutoStructify

project = 'conda-store'
copyright = '2022, Quansight'
author = 'Quansight'
release = '0.4.12'

extensions = [
    'recommonmark',
    'sphinx_panels',
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
            "url": "https://github.com/Quansight/conda-store",
            "icon": "fa-brands fa-github",
        }
   ],
}
html_sidebars = {
  "index": [],
}

def setup(app):
    app.add_config_value('recommonmark_config', {
        'enable_eval_rst': True,
    }, True)
    app.add_transform(AutoStructify)
