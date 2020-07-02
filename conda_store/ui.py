import threading
import datetime

from werkzeug.serving import make_server
from flask import jsonify, Flask


class ServerThread(threading.Thread):
    def __init__(self, conda_store, app, address, port):
        threading.Thread.__init__(self)
        self.srv = make_server(address, port, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        self.srv.serve_forever()

    def shutdown(self):
        self.srv.shutdown()


def start_ui_server(address='0.0.0.0', port=5000):
    app = Flask('conda_store_ui')
    server = ServerThread(app, address, port)
    server.start()

    @app.route('/')
    def index():
        return "This is the environment page"

    @app.route('/api/v1/')
    def api_status():
        return jsonify({"status": "ok"})

    @app.route('/api/v1/environment/')
    def list_environments():
        return ['asdf', 'qwer', 'zxcv']

    @app.route('/api/v1/environment/<name>/', methods=['GET'])
    def get_environment(name):
        return jsonify({'name': name, 'last_modified': datetime.datetime.now()})

    @app.route('/api/v1/environment/<name>/', methods=['PUT'])
    def update_environment(name):
        return jsonify({'name': name, 'last_modified': datetime.datetime.now()})

    @app.route('/api/v1/environment/<name>/', methods=['DELETE'])
    def delete_environment(name):
        return jsonify({'name': name, 'last_modified': datetime.datetime.now()})
