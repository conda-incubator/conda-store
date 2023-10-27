import requests


def get_environments(host="localhost", port="8080"):
    return requests.get(f"http://{host}:{port}/api/v1/environment/").json()


def get_environment_packages(name, host="localhost", port="8080"):
    return requests.get(f"http://{host}:{port}/api/v1/environment/{name}").json()


def post_specification(specification, host="localhost", port="8080"):
    return requests.post(
        f"http://{host}:{port}/api/v1/specification/", json=specification
    ).json()
