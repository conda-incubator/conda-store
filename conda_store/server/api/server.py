import datetime

from flask import jsonify, Flask, g, request, Response, redirect
import pydantic

from conda_store import api, schema
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
        environments = [schema.Environment.from_orm(_).dict() for _ in api.list_environments(conda_store.db)]
        return jsonify(environments)

    @app.route('/api/v1/environment/<name>/', methods=['GET'])
    def api_get_environment(name):
        conda_store = get_conda_store(store_directory, storage_backend)
        environment = schema.Environment.from_orm(api.get_environment(conda_store.db, name)).dict()
        return jsonify(environment)

    @app.route('/api/v1/specification/', methods=['GET'])
    def api_list_specification():
        conda_store = get_conda_store(store_directory, storage_backend)
        specifications = [schema.Specification.from_orm(_).dict(exclude={'builds'}) for _ in api.list_specifications(conda_store.db)]
        return jsonify(specifications)

    @app.route('/api/v1/specification/', methods=['POST'])
    def api_post_specification():
        conda_store = get_conda_store(store_directory, storage_backend)
        try:
            specification = schema.CondaSpecification.parse_obj(request.json)
            api.post_specification(conda_store, specification)
            return jsonify({'status': 'ok'})
        except pydantic.ValidationError as e:
            return jsonify({'status': 'error', 'error': e.errors()}), 400

    @app.route('/api/v1/specification/<sha256>/', methods=['GET'])
    def api_get_specification(sha256):
        conda_store = get_conda_store(store_directory, storage_backend)
        specification = schema.Specification.from_orm(api.get_specification(conda_store.db, sha256))
        return jsonify(specification.dict(exclude={'builds'}))

    @app.route('/api/v1/build/', methods=['GET'])
    def api_list_builds():
        conda_store = get_conda_store(store_directory, storage_backend)
        builds = [schema.Build.from_orm(build).dict(exclude={'packages'}) for build in api.list_builds(conda_store.db)]
        return jsonify(builds)

    @app.route('/api/v1/build/<build_id>/', methods=['GET'])
    def api_get_build(build_id):
        conda_store = get_conda_store(store_directory, storage_backend)
        build = schema.Build.from_orm(api.get_build(conda_store.db, build_id))
        return jsonify(build.dict())

    @app.route('/api/v1/build/<build_id>/logs/', methods=['GET'])
    def api_get_build_logs(build_id):
        conda_store = get_conda_store(store_directory, storage_backend)
        log_key = api.get_build(conda_store.db, build_id).log_key
        return redirect(conda_store.storage.get_url(log_key))

    @app.route('/api/v1/package/<provider>/', methods=['GET'])
    def api_list_packages(provider):
        conda_store = get_conda_store(store_directory, storage_backend)
        if provider == 'conda':
            packages = [schema.CondaPackage.from_orm(package).dict() for package in api.list_conda_packages(conda_store.db)]
            return jsonify(packages)
        else:
            raise ValueError(f'provider={provider} not supported')

    app.run(debug=True, host=address, port=port)
