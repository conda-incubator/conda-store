import requests


def get_environments(host='localhost', port='5000'):
    return requests.get(f'http://{host}:{port}/api/v1/environment/').json()


def post_specification(specification, host='localhost', port='5000'):
    return requests.post(
        f'http://{host}:{port}/api/v1/specification/',
        json=specification).json()
