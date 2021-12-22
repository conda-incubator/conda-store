import logging
import os
import sys

from flask import Flask
from flask.blueprints import Blueprint
from flask_cors import CORS
from traitlets import Bool, Unicode, Integer, Type, validate
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

    registry_external_url = Unicode(
        "localhost:5000",
        help='external hostname and port to access docker registry cannot contain "http://" or "https://"',
        config=True,
    )

    url_prefix = Unicode(
        "/",
        help="the prefix URL (subdirectory) for the entire application; "
        "it MUST start with a forward slash - tip: "
        "use this to run conda-store within an existing website.",
        config=True,
    )

    config_file = Unicode(
        help="config file to load for conda-store",
        config=True,
    )

    @validate("config_file")
    def _validate_config_file(self, proposal):
        if not os.path.isfile(proposal.value):
            print(
                "ERROR: Failed to find specified config file: {}".format(
                    proposal.value
                ),
                file=sys.stderr,
            )
            sys.exit(1)
        return proposal.value

    authentication_class = Type(
        default_value=auth.DummyAuthentication,
        klass=auth.Authentication,
        allow_none=False,
        config=True,
    )

    max_page_size = Integer(
        100, help="maximum number of items to return in a single page", config=True
    )

    def initialize(self, *args, **kwargs):
        super().initialize(*args, **kwargs)
        self.load_config_file(self.config_file)

    def start(self):
        app = Flask(__name__)
        cors_prefix = f"{self.url_prefix if self.url_prefix != '/' else ''}"
        CORS(
            app,
            resources={f"{cors_prefix}/api/v1/*": {"origins": "*"}},
        )

        if self.enable_api:
            app.register_blueprint(views.app_api, url_prefix=self.url_prefix)

        if self.enable_registry:
            # docker registry api specification does not support a url_prefix
            app.register_blueprint(views.app_registry)

        if self.enable_ui:
            app.register_blueprint(views.app_ui, url_prefix=self.url_prefix)

        if self.enable_metrics:
            app.register_blueprint(views.app_metrics, url_prefix=self.url_prefix)

        app.conda_store = CondaStore(parent=self, log=self.log)
        app.server = self
        app.authentication = self.authentication_class(parent=self, log=self.log)
        app.secret_key = app.authentication.authentication.secret

        @app.after_request
        def after_request_function(response):
            # force a new session on next request
            # since sessions are thread local
            app.conda_store.session_factory.remove()
            return response

        # add dynamic routes
        # NOTE: this will break`url_for`, since the method names behind each
        # route are not standardized; we build them "manually" by using `url_for`
        # pointing to the "/" (index) provider (right now is ui.ui_list_environments)
        # If the index function changes names, this will HAVE to be updated manually
        # on some templates too.

        app_auth = Blueprint("auth", self.authentication_class.__name__)
        for route, method, func in app.authentication.routes:
            app_auth.add_url_rule(route, func.__name__, func, methods=[method])
        app.register_blueprint(app_auth, url_prefix=self.url_prefix)

        app.conda_store.ensure_namespace()
        app.conda_store.ensure_conda_channels()

        # schedule tasks
        app.conda_store.celery_app

        from conda_store_server.worker import tasks

        (tasks.task_watch_paths.si()).apply_async()
        (tasks.task_update_storage_metrics.si()).apply_async()

        app.run(debug=True, host=self.address, port=self.port)
