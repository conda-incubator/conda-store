import datetime

from flask import jsonify, Flask, g


from conda_store.data_model import DatabaseManager, list_environments


def start_ui_server(conda_store, address='0.0.0.0', port=5000):
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

    @app.route('/')
    def index():
        return "This is the environment page"

    @app.route('/api/v1/')
    def api_status():
        return jsonify({"status": "ok"})

    @app.route('/api/v1/environment/')
    def _list_environments():
        dbm = get_dbm(conda_store)
        return jsonify(list_environments(dbm))

    @app.route('/api/v1/environment/<name>/', methods=['GET'])
    def get_environment(name):
        return jsonify({'name': name, 'last_modified': datetime.datetime.now()})

    @app.route('/api/v1/environment/<name>/', methods=['PUT'])
    def update_environment(name):
        return jsonify({'name': name, 'last_modified': datetime.datetime.now()})

    @app.route('/api/v1/environment/<name>/', methods=['DELETE'])
    def delete_environment(name):
        return jsonify({'name': name, 'last_modified': datetime.datetime.now()})

    app.run(debug=True, host=address, port=port)
