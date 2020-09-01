import datetime
import os
import importlib

from flask import jsonify, Flask, g, request, Response, render_template, redirect
import yaml

from conda_store.data_model.base import DatabaseManager
from conda_store.data_model import api
from conda_store.environments import validate_environment


def start_api_server(conda_store, address='0.0.0.0', port=5000):
    app = Flask(__name__, template_folder=os.path.join(os.path.dirname(importlib.__import__('conda_store.api.server').api.server.__file__), 'templates'))

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

    # api methods
    @app.route('/api/v1/')
    def api_status():
        return jsonify({"status": "ok"})

    @app.route('/api/v1/environment/')
    def api_list_environments():
        dbm = get_dbm(conda_store)
        return jsonify(api.list_environments(dbm))

    @app.route('/api/v1/environment/<environment>/')
    def api_get_environment(environment):
        dbm = get_dbm(conda_store)
        return jsonify(api.get_environment(dbm, environment))

    @app.route('/api/v1/specification/', methods=['GET'])
    def api_list_specification():
        dbm = get_dbm(conda_store)
        return jsonify(api.list_specifications(dbm))

    @app.route('/api/v1/specification/', methods=['POST'])
    def api_post_specification():
        dbm = get_dbm(conda_store)
        return jsonify(api.post_specifications(dbm, request.json))

    @app.route('/api/v1/specification/<spec>/', methods=['GET'])
    def api_get_specification(spec):
        dbm = get_dbm(conda_store)
        return jsonify(api.get_specification(dbm, spec))

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

    @app.route('/api/v1/environment/<name>/', methods=['DELETE'])
    def delete_environment(name):
        return jsonify({'name': name, 'last_modified': datetime.datetime.now()})

    # ui
    @app.route('/create/', methods=['GET'])
    def ui_create_get_environment():
        return render_template('create.html')

    @app.route('/create/', methods=['POST'])
    def ui_create_post_environment():
        try:
            spec = yaml.safe_load(request.form.get('specification', ''))
            if not validate_environment(spec):
                raise ValueError('non valid environment')
            dbm = get_dbm(conda_store)
            api.post_specification(dbm, spec)
            return redirect('/environment/')
        except (yaml.YAMLError, ValueError):
            return redirect('/create/')

    @app.route('/environment/', methods=['GET'])
    def ui_get_environments():
        dbm = get_dbm(conda_store)
        return render_template('environments.html', environments=api.list_environments(dbm))

    @app.route('/environment/<environment>/', methods=['GET'])
    def ui_get_environment(environment):
        dbm = get_dbm(conda_store)
        return render_template('environment.html', environment=api.get_environment(dbm, environment))

    @app.route('/specification/<spec>/', methods=['GET'])
    def ui_get_specification(spec):
        dbm = get_dbm(conda_store)
        specification = api.get_specification(dbm, spec)
        return render_template('specification.html', specification_id=spec, specification=specification, spec_str=yaml.dump(specification['spec']))

    @app.route('/build/<build>/', methods=['GET'])
    def ui_get_build(build):
        dbm = get_dbm(conda_store)
        return render_template('build.html', build_id=build, build=api.get_build(dbm, build))

    app.run(debug=True, host=address, port=port)
