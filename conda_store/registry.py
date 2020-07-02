import json

import requests
from flask import Flask, Response, redirect, g

from conda_store.data_model.base import DatabaseManager


def docker_token(image):
    url = f'https://auth.docker.io/token?service=registry.docker.io&scope=repository:{image}:pull'
    response = requests.get(url)
    return response.json()['token']


def docker_request_tags(image):
    token = docker_token(image)
    url = f'https://index.docker.io/v2/{image}/tags/list'
    return requests.get(url, headers={'Authorization': f'Bearer {token}'}).json()


def docker_request_mainfest(image, tag):
    token = docker_token(image)
    url = f'https://index.docker.io/v2/{image}/manifests/{tag}'
    return requests.get(url, headers={'Authorization': f'Bearer {token}'}).json()


def json_response(data, status=200, mimetype='application/json'):
    # doesn't like newlines in json strings
    response = Response(json.dumps(data).replace(r'\n', ''), status=status, mimetype=mimetype)
    response.headers['Docker-Distribution-Api-Version'] = 'registry/2.0'
    return response


def start_registry_server(conda_store, address='0.0.0.0', port=5001):
    app = Flask(__name__)

    def get_dbm(conda_store):
        dbm = getattr(g, '_dbm', None)
        if dbm is None:
            dbm = g._dbm = DatabaseManager(conda_store)
        return dbm

    @app.teardown_appcontext
    def close_connection(exception):
        dbm = getattr(g, '_dbm', None)
        if dbm is not None:
            dbm.close()

    @app.route("/v2/")
    def v2():
        return json_response({})

    @app.route("/v2/<path:rest>")
    def list_tags(rest):
        parts = rest.split('/')
        if len(parts) > 2 and parts[-2:] == ['tags', 'list']:
            image = '/'.join(parts[:-2])
            return json_response(docker_request_tags(image))
        elif len(parts) > 2 and parts[-2] == 'manifests':
            image = '/'.join(parts[:-2])
            tag = parts[-1]
            return json_response(docker_request_mainfest(image, tag), mimetype='application/vnd.docker.distribution.manifest.v1+prettyjws')
        elif len(parts) > 2 and parts[-2] == 'blobs':
            image = '/'.join(parts[:-2])
            blob = parts[-1]
            url = 'https://index.docker.io/v2/{image}/blobs/{blob}'
            return redirect(url)
        else:
            return json_response({'status': 'error', 'path': rest}, status=404)

    app.run(debug=True, host=address, port=port)
