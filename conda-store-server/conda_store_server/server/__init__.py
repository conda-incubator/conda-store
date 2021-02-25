from flask import Flask, g
from flask_cors import CORS

from conda_store_server.server import views
from conda_store_server.app import CondaStore


def start_app(
    store_directory,
    storage_backend,
    disable_ui=False,
    disable_api=False,
    disable_registry=False,
    address="0.0.0.0",
    port=5000,
):
    app = Flask(__name__)
    CORS(app, resources={r"/api/v1/*": {"origins": "*"}})

    if not disable_api:
        app.register_blueprint(views.app_api)

    if not disable_registry:
        app.register_blueprint(views.app_registry)

    if not disable_ui:
        app.register_blueprint(views.app_ui)

    @app.before_request
    def ensure_conda_store():
        conda_store = getattr(g, "_conda_store", None)
        if conda_store is None:
            g._conda_store = CondaStore(
                store_directory=store_directory,
                database_url=None,
                storage_backend=storage_backend,
            )

    app.run(debug=True, host=address, port=port)
