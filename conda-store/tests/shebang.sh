#!/usr/bin/env conda-store
#! conda-store run filesystem/python-flask-env:1 -- python

# filesystem/python-flask-env:1 is populated from tests/assets/environments/python-flask-env.yaml
import sys

assert sys.version_info[:2] == (3, 9)
import flask
print('shebang script ran')
