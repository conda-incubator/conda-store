import logging
import os
import sys

import uvicorn
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.templating import Jinja2Templates
from traitlets import Bool, Unicode, Integer, Type, validate, Instance, default
from traitlets.config import Application

from conda_store_server.server import auth, views
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

    behind_proxy = Bool(
        False,
        help="Indicates if server is behind web reverse proxy such as Nginx, Traefik, Apache. Will use X-Forward-.. headers to detemine scheme. Do not set to true if not behind proxy since Flask will trust any X-Forward-... header",
        config=True,
    )

    templates = Instance(
        help="Initialized fastapi.templating.Jinja2Templates to use for html templates",
        klass=Jinja2Templates,
        config=True,
    )

    @default("templates")
    def _default_templates(self):
        import conda_store_server.server
        templates_directory = os.path.join(
            os.path.dirname(conda_store_server.server.__file__),
            'templates')
        return Jinja2Templates(directory=templates_directory)

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
        conda_store = CondaStore(parent=self, log=self.log)
        authentication = self.authentication_class(parent=self, log=self.log)

        app = FastAPI()

        # if self.behind_proxy:
        #     app.wsgi_app = ProxyFix(app.wsgi_app)

        cors_prefix = f"{self.url_prefix if self.url_prefix != '/' else ''}"
        app.add_middleware(
            CORSMiddleware,
            allow_origins=['*'],
            allow_credentials=True,
        )
        app.add_middleware(
            SessionMiddleware,
            secret_key=authentication.authentication.secret)

        @app.middleware("http")
        async def conda_store_middleware(request: Request, call_next):
            try:
                request.state.conda_store = conda_store
                request.state.server = self
                request.state.authentication = authentication
                request.state.templates = self.templates
                response = await call_next(request)
            finally:
                request.state.conda_store.session_factory.remove()
            return response

        app.include_router(authentication.router)

        # if self.enable_api:
        #     app.register_blueprint(views.app_api, url_prefix=self.url_prefix)

        # if self.enable_registry:
        #     # docker registry api specification does not support a url_prefix
        #     app.register_blueprint(views.app_registry)

        if self.enable_ui:
            app.include_router(views.router_ui)

        # if self.enable_metrics:
        #     app.register_blueprint(views.app_metrics, url_prefix=self.url_prefix)

        # add dynamic routes
        # NOTE: this will break`url_for`, since the method names behind each
        # route are not standardized; we build them "manually" by using `url_for`
        # pointing to the "/" (index) provider (right now is ui.ui_list_environments)
        # If the index function changes names, this will HAVE to be updated manually
        # on some templates too.

        # app_auth = Blueprint("auth", self.authentication_class.__name__)
        # for route, method, func in app.authentication.routes:
        #     app_auth.add_url_rule(route, func.__name__, func, methods=[method])
        # app.register_blueprint(app_auth, url_prefix=self.url_prefix)

        conda_store.ensure_namespace()
        conda_store.ensure_conda_channels()

        # schedule tasks
        conda_store.celery_app

        from conda_store_server.worker import tasks  # noqa

        uvicorn.run(
            app,
            host=self.address,
            port=self.port,
            reload=False,
            debug=(self.log_level == logging.DEBUG),
            workers=1
        )
