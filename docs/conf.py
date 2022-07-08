import recommonmark
from recommonmark.transform import AutoStructify

project = 'conda-store'
copyright = '2022, Quansight'
author = 'Quansight'
release = '0.4.5'

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
