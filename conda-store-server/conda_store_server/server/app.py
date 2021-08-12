import logging

from flask import Flask
from flask_cors import CORS
from traitlets import Bool, Unicode, Integer, Type
from traitlets.config import Application

from conda_store_server.server import views, auth
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

    authentication_class = Type(
        default_value=auth.DummyAuthentication,
        klass=auth.Authentication,
        allow_none=False,
        config=True,
    )

    secret_key = Unicode(
        "super_secret_key",
        config=True,
        help="A secret key needed for some authentication methods, session storage, etc.",
    )

    def initialize(self, *args, **kwargs):
        super().initialize(*args, **kwargs)
        self.load_config_file(self.config_file)

    def start(self):
        app = Flask(__name__)
        CORS(app, resources={r"/api/v1/*": {"origins": "*"}})
        app.secret_key = self.secret_key

        if self.enable_api:
            app.register_blueprint(views.app_api)

        if self.enable_registry:
            app.register_blueprint(views.app_registry)

        if self.enable_ui:
            app.register_blueprint(views.app_ui)

        if self.enable_metrics:
            app.register_blueprint(views.app_metrics)

        app.conda_store = CondaStore(parent=self, log=self.log)
        app.authentication = self.authentication_class(parent=self, log=self.log)

        # add dynamic routes
        for route, method, func in app.authentication.routes:
            app.add_url_rule(route, func.__name__, func, methods=[method])

        app.conda_store.ensure_namespace()
        app.conda_store.ensure_directories()
        app.conda_store.configuration.update_storage_metrics(
            app.conda_store.db, app.conda_store.store_directory
        )
        # app.conda_store.ensure_conda_channels()

        app.run(debug=True, host=self.address, port=self.port)
