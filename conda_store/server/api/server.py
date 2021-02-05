import datetime

from flask import jsonify, Flask, g, request, Response

from conda_store import api
from conda_store.app import CondaStore


def start_api_server(store_directory, storage_backend, address='0.0.0.0', port=5001):
    app = Flask(__name__)

    def get_conda_store(store_directory, storage_backend):
        conda_store = getattr(g, '_conda_store', None)
        if conda_store is None:
            conda_store = g._conda_store = CondaStore(
                store_directory=store_directory,
                database_url=None,
                storage_backend=storage_backend)
        return conda_store

    # api methods
    @app.route('/api/v1/')
    def api_status():
        return jsonify({"status": "ok"})

    @app.route('/api/v1/environment/')
    def api_list_environments():
        conda_store = get_conda_store(store_directory, storage_backend)
        return jsonify([for environment in api.list_environments(conda_store.db)])

    @app.route('/api/v1/environment/<name>/', methods=['DELETE'])
    def api_get_environment(name):
        dbm = get_dbm(conda_store)
        return jsonify({'name': name, 'last_modified': datetime.datetime.now()})

    @app.route('/api/v1/specification/', methods=['GET'])
    def api_list_specification():
        dbm = get_dbm(conda_store)
        return jsonify(api.list_specifications(dbm))

    @app.route('/api/v1/specification/', methods=['POST'])
    def api_post_specification():
        dbm = get_dbm(conda_store)
        return jsonify(api.post_specification(dbm, request.json))

    @app.route('/api/v1/specification/<sha256>/', methods=['GET'])
    def api_get_specification(sha256):
        dbm = get_dbm(conda_store)
        return jsonify(api.get_specification(dbm, sha256))

    @app.route('/api/v1/build/<build>/', methods=['GET'])
    def api_get_build(build):
        dbm = get_dbm(conda_store)
        return jsonify(api.get_build(dbm, build))

    @app.route('/api/v1/build/<build>/logs/', methods=['GET'])
    def api_get_build_logs(build):
        dbm = get_dbm(conda_store)
        return Response(
            api.get_build_logs(dbm, build),
            mimetype='text/plain')

    @app.route('/api/v1/package/<provider>/', methods=['GET'])
    def api_list_packages(provider):
        dbm = get_dbm(conda_store)
        if provider == 'conda':
            return jsonify(api.list_conda_packages(dbm))
        else:
            raise ValueError(f'provider={provider} not supported')

    app.run(debug=True, host=address, port=port)
