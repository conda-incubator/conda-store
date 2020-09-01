import json

from flask import Flask, Response
import requests


def _docker_token(image):
    url = f'https://auth.docker.io/token?service=registry.docker.io&scope=repository:{image}:pull'
    response = requests.get(url)
    return response.json()['token']


def _docker_request_tags(image):
    token = _docker_token(image)
    url = f'https://index.docker.io/v2/{image}/tags/list'
    return requests.get(url, headers={'Authorization': f'Bearer {token}'}).json()


def _docker_request_manifest(image, tag):
    token = _docker_token(image)
    url = f'https://index.docker.io/v2/{image}/manifests/{tag}'
    response = requests.get(url, headers={'Authorization': f'Bearer {token}'})
    return response.json()


def _download_blob(image, blob):
    token = _docker_token(image)
    url = f'https://index.docker.io/v2/{image}/blobs/{blob}'
    response = requests.get(url, headers={'Authorization': f'Bearer {token}'})
    return response.content


def _json_response(data, status=200, mimetype='application/json'):
    response = Response(json.dumps(data, indent=3), status=status, mimetype=mimetype)
    response.headers['Docker-Distribution-Api-Version'] = 'registry/2.0'
    return response


def start_registry_server(conda_store, address='0.0.0.0', port=5002):
    app = Flask(__name__)

    @app.route("/v2/")
    def v2():
        return _json_response({})

    @app.route("/v2/<path:rest>")
    def list_tags(rest):
        parts = rest.split('/')
        if len(parts) > 2 and parts[-2:] == ['tags', 'list']:
            image = '/'.join(parts[:-2])
            return _json_response(_docker_request_tags(image))
        elif len(parts) > 2 and parts[-2] == 'manifests':
            image = '/'.join(parts[:-2])
            tag = parts[-1]
            return _json_response(_docker_request_manifest(image, tag), mimetype='application/json')
        elif len(parts) > 2 and parts[-2] == 'blobs':
            image = '/'.join(parts[:-2])
            blob = parts[-1]
            return (_download_blob(image, blob), 200, {'Docker-Distribution-Api-Version': 'registry/2.0'})
        else:
            return _json_response({'status': 'error', 'path': rest}, status=404)

    app.run(debug=True, host=address, port=port)
