import os
import traceback

from flask import Flask, g, request, render_template, redirect, Response, send_file
import yaml

from conda_store import api
from conda_store.app import CondaStore


def start_ui_server(store_directory, storage_backend, address='0.0.0.0', port=5000):
    app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))

    def get_conda_store(store_directory, storage_backend):
        conda_store = getattr(g, '_conda_store', None)
        if conda_store is None:
            conda_store = g._conda_store = CondaStore(
                store_directory=store_directory,
                database_url=None,
                storage_backend=storage_backend)
        return conda_store

    @app.route('/create/', methods=['GET', 'POST'])
    def ui_create_get_environment():
        if request.method == 'GET':
            return render_template('create.html')
        elif request.method == 'POST':
            try:
                spec = yaml.safe_load(request.form.get('specification'))
                conda_store = get_conda_store(store_directory, storage_backend)
                api.post_specification(conda_store, spec)
                return redirect('/')
            except (yaml.YAMLError, ValueError):
                return render_template('create.html', spec=yaml.dump(spec), message=traceback.format_exc())

    @app.route('/', methods=['GET'])
    def ui_get_environments():
        conda_store = get_conda_store(store_directory, storage_backend)
        return render_template('home.html',
                               environments=api.list_environments(conda_store.db),
                               metrics=api.get_metrics(conda_store.db))

    @app.route('/environment/<name>/', methods=['GET'])
    def ui_get_environment(name):
        conda_store = get_conda_store(store_directory, storage_backend)
        return render_template('environment.html',
                               environment=api.get_environment(conda_store.db, name),
                               envionment_builds=api.get_environment(conda_store.db, name))

    @app.route('/environment/<name>/edit/', methods=['GET'])
    def ui_edit_environment(name):
        conda_store = get_conda_store(store_directory, storage_backend)
        environment = api.get_environment(conda_store.db, name)
        specification = api.get_specification(conda_store.db, environment.sha256)
        return render_template('create.html', spec=yaml.dump(specification.spec))

    @app.route('/specification/<sha256>/', methods=['GET'])
    def ui_get_specification(sha256):
        conda_store = get_conda_store(store_directory, storage_backend)
        specification = api.get_specification(conda_store.db, sha256)
        return render_template('specification.html', specification=specification, spec=yaml.dump(specification.spec))

    @app.route('/build/<build_id>/', methods=['GET'])
    def ui_get_build(build_id):
        conda_store = get_conda_store(store_directory, storage_backend)
        build = api.get_build(conda_store.db, build_id)
        return render_template('build.html', build=build)

    @app.route('/build/<build_id>/logs/', methods=['GET'])
    def api_get_build_logs(build_id):
        conda_store = get_conda_store(store_directory, storage_backend)
        log_key = api.get_build(conda_store.db, build_id).log_key
        return redirect(conda_store.storage.get_url(log_key))

    @app.route('/build/<build_id>/lockfile/', methods=['GET'])
    def api_get_build_lockfile(build_id):
        conda_store = get_conda_store(store_directory, storage_backend)
        lockfile = api.get_build_lockfile(conda_store.db, build_id)
        return Response(lockfile, mimetype='text/plain')

    @app.route('/build/<build_id>/archive/', methods=['GET'])
    def api_get_build_archive(build_id):
        conda_store = get_conda_store(store_directory, storage_backend)
        conda_pack_key = api.get_build(conda_store.db, build_id).conda_pack_key
        return redirect(conda_store.storage.get_url(conda_pack_key))

    @app.route('/build/<build>/docker/', methods=['GET'])
    def api_get_build_docker_archive(build):
        dbm = get_dbm(conda_store)
        data = api.get_build_docker_archive(dbm, build)
        archive_download_filename = f'{data["spec_sha256"]}-{data["name"]}.docker.tar'
        return send_file(data['docker_path'], mimetype='application/x-tar', as_attachment=True, attachment_filename=archive_download_filename)

    app.run(debug=True, host=address, port=port)
