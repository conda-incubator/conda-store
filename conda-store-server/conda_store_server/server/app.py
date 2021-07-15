import logging

from flask import Flask, g
from flask_cors import CORS
from traitlets import Bool, Unicode, Integer
from traitlets.config import Application

from conda_store_server.server import views
from conda_store_server.app import CondaStore


class CondaStoreServer(Application):
    aliases = {
        "config": "CondaStoreServer.config_file",
    }

    log_level = Integer(
        logging.INFO,
        help="log level to use",
        config=True,
    )

    enable_ui = Bool(True, help="serve the web ui for conda-store", config=True)

    enable_api = Bool(
        True,
        help="enable the rest api for conda-store",
        config=True,
    )

    enable_registry = Bool(
        True, help="enable the docker registry for conda-store", config=True
    )

    enable_metrics = Bool(
        True,
        help="enable the prometheus metrics for conda-store",
        config=True,
    )

    address = Unicode(
        "0.0.0.0", help="ip address or hostname for conda-store server", config=True
    )

    port = Integer(5000, help="port for conda-store server", config=True)

    config_file = Unicode(
        "conda_store_config.py", help="config file to load for conda-store", config=True
    )

    def initialize(self, *args, **kwargs):
        super().initialize(*args, **kwargs)
        self.log.info(f"reading configuration file {self.config_file}")
        self.load_config_file(self.config_file)

    def start(self):
        app = Flask(__name__)
        CORS(app, resources={r"/api/v1/*": {"origins": "*"}})

        if self.enable_api:
            app.register_blueprint(views.app_api)

        if self.enable_registry:
            app.register_blueprint(views.app_registry)

        if self.enable_ui:
            app.register_blueprint(views.app_ui)

        if self.enable_metrics:
            app.register_blueprint(views.app_metrics)

        @app.before_request
        def ensure_conda_store():
            if not hasattr(g, "_conda_store"):
                g._conda_store = CondaStore(parent=self, log=self.log)

        app.run(debug=True, host=self.address, port=self.port)
