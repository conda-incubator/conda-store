import datetime

from flask import jsonify, Flask

app = Flask()


@app.route('/')
def index():
    return "This is the environment page"


@app.route('/api/v1/')
def api_status():
    return jsonify({"status": "ok"})


@app.route('/api/v1/environment/')
def list_environments():
    return ['asdf', 'qwer', 'zxcv']


@app.route('/api/v1/enviornment/<name>/', method='GET')
def get_environment(name):
    return jsonify({'name': name, 'last_modified': datetime.datetime.now()})


@app.route('/api/v1/enviornment/<name>/', method='PUT')
def update_environment(name):
    return jsonify({'name': name, 'last_modified': datetime.datetime.now()})


@app.route('/api/v1/enviornment/<name>/', method='DELETE')
def delete_environment(name):
    return jsonify({'name': name, 'last_modified': datetime.datetime.now()})
