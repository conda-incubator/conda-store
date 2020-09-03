import os
import traceback

from flask import Flask, g, request, render_template, redirect, Response, send_file
import yaml

from conda_store.data_model.base import DatabaseManager
from conda_store.data_model import api
from conda_store.environments import validate_environment


def start_ui_server(conda_store, address='0.0.0.0', port=5000):
    app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))

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

    @app.route('/create/', methods=['GET', 'POST'])
    def ui_create_get_environment():
        if request.method == 'GET':
            return render_template('create.html')
        elif request.method == 'POST':
            try:
                spec = yaml.safe_load(request.form.get('specification'))
                dbm = get_dbm(conda_store)
                api.post_specification(dbm, spec)
                return redirect('/environment/')
            except (yaml.YAMLError, ValueError):
                return render_template('create.html', spec=yaml.dump(spec), message=traceback.format_exc())

    @app.route('/', methods=['GET'])
    def ui_get_environments():
        dbm = get_dbm(conda_store)
        return render_template('home.html',
                               environments=api.list_environments(dbm),
                               metrics=api.get_metrics(conda_store))

    @app.route('/environment/<name>/', methods=['GET'])
    def ui_get_environment(name):
        dbm = get_dbm(conda_store)
        return render_template('environment.html', environment=api.get_environment(dbm, name))

    @app.route('/environment/<name>/edit/', methods=['GET'])
    def ui_edit_environment(name):
        dbm = get_dbm(conda_store)
        environment = api.get_environment(dbm, name)
        specification = api.get_specification(dbm, environment['spec_sha256'])
        return render_template('create.html', spec=yaml.dump(specification['spec']))

    @app.route('/specification/<sha256>/', methods=['GET'])
    def ui_get_specification(sha256):
        dbm = get_dbm(conda_store)
        specification = api.get_specification(dbm, sha256)
        return render_template('specification.html', specification=specification, spec=yaml.dump(specification['spec']))

    @app.route('/build/<build>/', methods=['GET'])
    def ui_get_build(build):
        dbm = get_dbm(conda_store)
        return render_template('build.html', build_id=build, build=api.get_build(dbm, build))

    @app.route('/build/<build>/logs/', methods=['GET'])
    def api_get_build_logs(build):
        dbm = get_dbm(conda_store)
        return Response(api.get_build_logs(dbm, build), mimetype='text/plain')

    @app.route('/build/<build>/lockfile/', methods=['GET'])
    def api_get_build_lockfile(build):
        dbm = get_dbm(conda_store)
        return Response(api.get_build_lockfile(dbm, build), mimetype='text/plain')

    @app.route('/build/<build>/archive/', methods=['GET'])
    def api_get_build_archive(build):
        dbm = get_dbm(conda_store)
        data = api.get_build_archive(dbm, build)
        archive_download_filename = f'{data["spec_sha256"]}-{data["name"]}.tar.gz'
        return send_file(data['archive_path'], mimetype='application/gzip', as_attachment=True, attachment_filename=archive_download_filename)

    app.run(debug=True, host=address, port=port)
