from flask import g


def get_conda_store():
    return g._conda_store
