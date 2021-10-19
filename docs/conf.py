import recommonmark
from recommonmark.transform import AutoStructify

project = 'conda-store'
copyright = '2021, Chris Ostrouchov'
author = 'Chris Ostrouchov'
release = '0.1.0'

extensions = [
    'recommonmark',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = "pydata_sphinx_theme"
html_static_path = ['_static']

def setup(app):
    app.add_config_value('recommonmark_config', {
        'enable_eval_rst': True,
    }, True)
    app.add_transform(AutoStructify)
