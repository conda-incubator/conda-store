import logging
import os
import sys

import conda_store_server
import conda_store_server.dbutil as dbutil
import uvicorn
from conda_store_server import __version__, storage
from conda_store_server.app import CondaStore
from conda_store_server.server import auth, views
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from traitlets import (
    Bool,
    Dict,
    Instance,
    Integer,
    List,
    Type,
    Unicode,
    default,
    validate,
)
from traitlets.config import Application, catch_config_error


class CondaStoreServer(Application):
    aliases = {
        "config": "CondaStoreServer.config_file",
    }

    flags = {
        "standalone": (
            {
                "CondaStoreServer": {
                    "standalone": True,
                }
            },
            "Run conda-store-server in standalone mode with celery worker as a subprocess of webserver",
        ),
    }

    reload = Bool(
        False,
        help="Enable reloading on code change",
        config=True,
    )

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

    template_vars = Dict(
        {},
        help="Extra variables to be passed into jinja templates for page rendering",
        config=True,
    )

    additional_routes = List(
        [],
        help="Additional routes for conda-store to serve [(path, method, function), ...]",
        config=True,
    )

    cors_allow_origins = List(
        [], help="list of allowed origins for CORS requests", config=True
    )

    cors_allow_origin_regex = Unicode(
        ".*",
        help="regex string to match against origins that should be permitted to make cross-origin requests",
        config=True,
        allow_none=True,
    )

    @default("templates")
    def _default_templates(self):
        import conda_store_server.server

        templates_directory = os.path.join(
            os.path.dirname(conda_store_server.server.__file__), "templates"
        )
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

    standalone = Bool(
        False,
        help="Run application in standalone mode with workers running as subprocess",
        config=True,
    )

    @catch_config_error
    def initialize(self, *args, **kwargs):
        super().initialize(*args, **kwargs)
        self.load_config_file(self.config_file)

        self.conda_store = CondaStore(parent=self, log=self.log)

        if self.conda_store.upgrade_db:
            dbutil.upgrade(self.conda_store.database_url)

        self.authentication = self.authentication_class(
            parent=self,
            log=self.log,
            authentication_db=self.conda_store.session_factory,
        )

        # ensure checks on redis_url
        self.conda_store.redis_url

    def init_fastapi_app(self):
        def trim_slash(url):
            return url[:-1] if url.endswith("/") else url

        app = FastAPI(
            title="conda-store",
            version=__version__,
            openapi_url=os.path.join(self.url_prefix, "openapi.json"),
            docs_url=os.path.join(self.url_prefix, "docs"),
            redoc_url=os.path.join(self.url_prefix, "redoc"),
            contact={
                "name": "Quansight",
                "url": "https://quansight.com",
            },
            license_info={
                "name": "BSD 3-Clause",
                "url": "https://opensource.org/licenses/BSD-3-Clause",
            },
        )

        app.add_middleware(
            CORSMiddleware,
            allow_origins=self.cors_allow_origins,
            allow_origin_regex=self.cors_allow_origin_regex,
            allow_credentials=True,
            allow_headers=["*"],
            allow_methods=["*"],
        )
        app.add_middleware(
            SessionMiddleware, secret_key=self.authentication.authentication.secret
        )

        # ensure that template variables are inserted into templates
        self.templates.env.globals.update(self.template_vars)

        @app.middleware("http")
        async def conda_store_middleware(request: Request, call_next):
            request.state.conda_store = self.conda_store
            request.state.server = self
            request.state.authentication = self.authentication
            request.state.templates = self.templates
            response = await call_next(request)
            return response

        @app.exception_handler(HTTPException)
        async def http_exception_handler(request, exc):
            return JSONResponse(
                {
                    "status": "error",
                    "message": exc.detail,
                },
                status_code=exc.status_code,
            )

        app.include_router(
            self.authentication.router,
            prefix=trim_slash(self.url_prefix),
        )

        if self.enable_api:
            app.include_router(
                views.router_api,
                prefix=trim_slash(self.url_prefix),
            )

        if self.enable_registry:
            # docker registry api specification does not support a url_prefix
            app.include_router(views.router_registry)

        if self.enable_ui:
            app.include_router(
                views.router_ui,
                prefix=trim_slash(self.url_prefix) + "/admin",
            )

            app.include_router(
                views.router_conda_store_ui,
                prefix=trim_slash(self.url_prefix),
            )

            # serving static files
            import conda_store_server.server

            app.mount(
                trim_slash(self.url_prefix) + "/static/",
                StaticFiles(
                    directory=os.path.join(
                        os.path.dirname(conda_store_server.server.__file__),
                        "static",
                    ),
                ),
                name="static",
            )

            # convenience to redirect "/" to home page when using a prefix
            # realistically this url will not be hit with a proxy + prefix
            if self.url_prefix != "/":

                @app.get("/")
                def redirect_home(request: Request):
                    return RedirectResponse(request.url_for("get_conda_store_ui"))

            @app.get("/favicon.ico", include_in_schema=False)
            async def favicon():
                return FileResponse(
                    os.path.join(
                        os.path.dirname(conda_store_server.server.__file__),
                        "static",
                        "favicon.ico",
                    )
                )

        if self.enable_metrics:
            app.include_router(
                views.router_metrics,
                prefix=trim_slash(self.url_prefix),
            )

        if self.additional_routes:
            for path, method, func in self.additional_routes:
                getattr(app, method)(path, name=func.__name__)(func)

        if isinstance(self.conda_store.storage, storage.LocalStorage):
            self.conda_store.storage.storage_url = (
                f"{trim_slash(self.url_prefix)}/storage"
            )
            app.mount(
                self.conda_store.storage.storage_url,
                StaticFiles(directory=self.conda_store.storage.storage_path),
                name="static-storage",
            )

        return app

    def start(self):
        fastapi_app = self.init_fastapi_app()

        with self.conda_store.session_factory() as db:
            self.conda_store.ensure_settings(db)
            self.conda_store.ensure_namespace(db)
            self.conda_store.ensure_conda_channels(db)

        # start worker if in standalone mode
        if self.standalone:
            import multiprocessing

            multiprocessing.set_start_method("spawn")

            from conda_store_server.worker.app import CondaStoreWorker

            process = multiprocessing.Process(target=CondaStoreWorker.launch_instance)
            process.start()

        try:
            uvicorn.run(
                fastapi_app,
                host=self.address,
                port=self.port,
                workers=1,
                proxy_headers=self.behind_proxy,
                forwarded_allow_ips=("*" if self.behind_proxy else None),
                reload=self.reload,
                reload_dirs=(
                    [os.path.dirname(conda_store_server.__file__)]
                    if self.reload
                    else []
                ),
            )
        finally:
            if self.standalone:
                process.join()
