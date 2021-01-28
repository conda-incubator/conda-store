import json

from flask import Flask, Response, redirect

from conda_store.storage import S3Storage, LocalStorage


def _json_response(data, status=200, mimetype='application/json'):
    response = Response(json.dumps(data, indent=3), status=status, mimetype=mimetype)
    response.headers['Docker-Distribution-Api-Version'] = 'registry/2.0'
    return response


def start_registry_server(conda_store, storage_backend, address='0.0.0.0', port=5002):
    if storage_backend == 's3':
        storage_manager = S3Storage()
    else: # filesystem
        # storage_manager = LocalStorage(store_directory / 'storage', 'http://..../')
        raise NotImplementedError('filesystem as a storage_manager not implemented')

    app = Flask(__name__)

    @app.route("/v2/")
    def v2():
        return _json_response({})

    @app.route("/v2/<path:rest>")
    def list_tags(rest):
        parts = rest.split('/')
        if len(parts) > 2 and parts[-2:] == ['tags', 'list']:
            image = '/'.join(parts[:-2])
            raise NotImplementedError()
        elif len(parts) > 2 and parts[-2] == 'manifests':
            image = '/'.join(parts[:-2])
            tag = parts[-1]
            manifests_key = f'docker/manifest/{image}/{tag}'
            return redirect(storage_manager.get_url(manifests_key))
        elif len(parts) > 2 and parts[-2] == 'blobs':
            image = '/'.join(parts[:-2])
            blob = parts[-1]
            blob_key = f'docker/blobs/{blob}'
            return redirect(storage_manager.get_url(blob_key))
        else:
            return _json_response({'status': 'error', 'path': rest}, status=404)

    app.run(debug=True, host=address, port=port)
