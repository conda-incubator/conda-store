import enum
from os import access
import re
import secrets
import datetime
from time import sleep


import jwt
import requests
from traitlets.config import LoggingConfigurable
from traitlets import Dict, Unicode, Type
from flask import (
    request,
    render_template,
    redirect,
    g,
    abort,
    jsonify,
    session,
    url_for,
)
from sqlalchemy import or_, and_
from werkzeug.utils import import_string

from conda_store_server import schema, orm


ARN_ALLOWED_REGEX = re.compile(r"^([A-Za-z\_\-\*]+)/([A-Za-z\_\-\*]+)$")


class Permissions(enum.Enum):
    ENVIRONMENT_CREATE = "build::create"
    ENVIRONMENT_READ = "build::read"
    ENVIRONMENT_UPDATE = "build::update"
    ENVIRONMENT_DELETE = "build::delete"


class AuthenticationBackend(LoggingConfigurable):
    secret = Unicode(
        secrets.token_hex(128),
        help="symetric secret to use for encrypting tokens",
        config=True,
    )

    jwt_algorithm = Unicode(
        "HS256",
        help="jwt algorithm to use for encryption/decryption",
        config=True,
    )

    @property
    def routes(self):
        raise NotImplementedError()

    def encrypt_token(self, token: schema.AuthenticationToken):
        return jwt.encode(token.dict(), self.secret, algorithm=self.jwt_algorithm)

    def decrypt_token(self, token: str):
        return jwt.decode(token, self.secret, algorithms=[self.jwt_algorithm])

    def authenticate(self, token):
        try:
            return schema.AuthenticationToken.parse_obj(self.decrypt_token(token))
        except Exception:
            return None


class RBACAuthorizationBackend(LoggingConfigurable):
    role_mappings = Dict(
        {
            "viewer": {Permissions.ENVIRONMENT_READ},
            "developer": {
                Permissions.ENVIRONMENT_CREATE,
                Permissions.ENVIRONMENT_READ,
                Permissions.ENVIRONMENT_UPDATE,
            },
            "admin": {
                Permissions.ENVIRONMENT_CREATE,
                Permissions.ENVIRONMENT_READ,
                Permissions.ENVIRONMENT_UPDATE,
                Permissions.ENVIRONMENT_DELETE,
            },
        },
        help="default role to permissions mapping to use",
        config=True,
    )

    unauthenticated_role_bindings = Dict(
        {
            "default/*": {"viewer"},
        },
        help="default roles bindings to asign to unauthenticated users",
        config=True,
    )

    authenticated_role_bindings = Dict(
        {
            "default/*": {"viewer"},
            "filesystem/*": {"viewer"},
        },
        help="default permissions to apply to specific resources",
    )

    @staticmethod
    def compile_arn_regex(arn):
        """Take an arn of form "example-*/example-*" and compile to regular expression"""
        if not ARN_ALLOWED_REGEX.match(arn):
            raise ValueError(f"invalid arn={arn}")

        regex_arn = "^" + re.sub(r"\*", r"[A-Za-z_\-]*", arn) + "$"
        return re.compile(regex_arn)

    @staticmethod
    def compile_arn_sql_like(arn):
        match = ARN_ALLOWED_REGEX.match(arn)
        if match is None:
            raise ValueError(f"invalid arn={arn}")

        return re.sub(r"\*", "%", match.group(1)), re.sub(r"\*", "%", match.group(2))

    def get_entity_bindings(self, entity_bindings, authenticated=False):
        if authenticated:
            return {
                **self.authenticated_role_bindings,
                **entity_bindings,
            }
        else:
            return {
                **self.unauthenticated_role_bindings,
                **entity_bindings,
            }

    def entity_roles(self, arn, entity_bindings, authenticated=False):
        entity_bindings = self.get_entity_bindings(entity_bindings, authenticated)

        roles = set()
        for entity_arn, entity_roles in entity_bindings.items():
            if self.compile_arn_regex(entity_arn).match(arn):
                roles = roles | set(entity_roles)
        return roles

    def convert_roles_to_permissions(self, roles):
        permissions = set()
        for role in roles:
            permissions = permissions | self.role_mappings[role]
        return permissions

    def authorize(self, entity_bindings, arn, permissions, authenticated=False):
        entity_bindings = self.get_entity_bindings(entity_bindings, authenticated)
        roles = self.entity_roles(arn, entity_bindings)
        return permissions <= self.convert_roles_to_permissions(roles)


class Authentication(LoggingConfigurable):
    cookie_name = Unicode(
        "conda-store-auth",
        help="name of cookie used for authentication",
        config=True,
    )

    authentication_backend = Type(
        AuthenticationBackend,
        help="class for authentication implementation",
        config=True,
    )

    authorization_backend = Type(
        RBACAuthorizationBackend,
        help="class for authorization implementation",
        config=True,
    )

    login_html = Unicode(
        """
<div class="text-center">
    <form class="form-signin" method="POST">
        <h1 class="h3 mb-3 fw-normal">Please sign in</h1>
        <div class="form-floating">
            <input name="username" class="form-control" id="floatingInput" placeholder="Username">
            <label for="floatingInput">Username</label>
        </div>
        <div class="form-floating">
            <input name="password" type="password" class="form-control" id="floatingPassword" placeholder="Password">
            <label for="floatingPassword">Password</label>
        </div>
        <button class="w-100 btn btn-lg btn-primary" type="submit">{SIGN_IN_BUTTON_TEXT}</button>
    </form>
</div>
        """,
        help="html form to use for login",
        config=True,
    )

    sign_in_button_text = Unicode(
        "Sign In",
        config=True,
        help="Text that will be displayed in the Sign In button.",
    )

    @property
    def authentication(self):
        if hasattr(self, "_authentication"):
            return self._authentication
        self._authentication = self.authentication_backend(parent=self, log=self.log)
        return self._authentication

    @property
    def authorization(self):
        if hasattr(self, "_authorization"):
            return self._authorization
        self._authorization = self.authorization_backend(parent=self, log=self.log)
        return self._authorization

    @property
    def routes(self):
        return [
            ("/login/", "GET", self.get_login_method),
            ("/login/", "POST", self.post_login_method),
            ("/logout/", "POST", self.post_logout_method),
        ]

    def authenticate(self, request):
        return schema.AuthenticationToken(
            primary_namespace="default",
            role_bindings={
                "*/*": ["admin"],
            },
        )

    def get_login_method(self):
        return render_template(
            "login.html",
            login_html=self.login_html.format(
                SIGN_IN_BUTTON_TEXT=self.sign_in_button_text
            ),
        )

    def post_login_method(self):
        redirect_url = request.args.get("next", "/")
        response = redirect(redirect_url)
        authentication_token = self.authenticate(request)
        if authentication_token is None:
            abort(
                jsonify(
                    {"status": "error", "message": "invalid authentication credentials"}
                ),
                403,
            )

        response.set_cookie(
            self.cookie_name,
            self.authentication.encrypt_token(authentication_token),
            httponly=True,
            samesite="strict",
            # set cookie to expire at same time as jwt
            max_age=(authentication_token.exp - datetime.datetime.utcnow()).seconds,
        )
        return response

    def post_logout_method(self):
        redirect_url = request.args.get("next", "/")
        response = redirect(redirect_url)
        response.set_cookie(self.cookie_name, "", expires=0)
        return response

    def authenticate_request(self, require=False):
        if hasattr(g, "entity"):
            pass  # only authenticate once
        elif request.cookies.get(self.cookie_name):
            # cookie based authentication
            token = request.cookies.get(self.cookie_name)
            g.entity = self.authentication.authenticate(token)
        elif request.headers.get("Authorization"):
            # auth bearer based authentication
            token = request.headers.get("Authorization").split(" ")[1]
            g.entity = self.authentication.authenticate(token)
        else:
            g.entity = None

        if require and g.entity is None:
            response = jsonify(
                {"status": "error", "message": "request not authenticated"}
            )
            response.status_code = 401
            abort(response)

        return g.entity

    @property
    def entity_bindings(self):
        entity = self.authenticate_request()
        return self.authorization.get_entity_bindings(
            {} if entity is None else entity.role_bindings, entity is not None
        )

    def authorize_request(self, arn, permissions, require=False):
        if not hasattr(g, "entity"):
            self.authenticate_request()

        if not hasattr(g, "authorized"):
            role_bindings = {} if (g.entity is None) else g.entity.role_bindings
            g.authorized = self.authorization.authorize(
                role_bindings, arn, permissions, g.entity is not None
            )

        if require and not g.authorized:
            response = jsonify({"status": "error", "message": "request not authorized"})
            response.status_code = 403
            abort(response)

        return g.authorized

    def filter_builds(self, query):
        cases = []
        for entity_arn, entity_roles in self.entity_bindings.items():
            namespace, name = self.authorization.compile_arn_sql_like(entity_arn)
            cases.append(
                and_(
                    orm.Namespace.name.like(namespace),
                    orm.Specification.name.like(name),
                )
            )

        if not cases:
            return query.filter(False)

        return (
            query.join(orm.Build.namespace)
            .join(orm.Build.specification)
            .filter(or_(*cases))
        )

    def filter_environments(self, query):
        cases = []
        for entity_arn, entity_roles in self.entity_bindings.items():
            namespace, name = self.authorization.compile_arn_sql_like(entity_arn)
            cases.append(
                and_(
                    orm.Namespace.name.like(namespace), orm.Environment.name.like(name)
                )
            )

        if not cases:
            return query.filter(False)

        return query.join(orm.Environment.namespace).filter(or_(*cases))

    def filter_namespaces(self, query):
        cases = []
        for entity_arn, entity_roles in self.entity_bindings.items():
            namespace, name = self.authorization.compile_arn_sql_like(entity_arn)
            cases.append(orm.Namespace.name.like(namespace))

        if not cases:
            return query.filter(False)

        return query.filter(or_(*cases))


class DummyAuthentication(Authentication):
    """Dummy Authentication for testing
    By default, any username + password is allowed
    If a non-empty password is set, any username will be allowed
    if it logs in with that password.
    """

    password = Unicode(
        "password",
        config=True,
        help="""
        Set a global password for all users wanting to log in.
        This allows users with any username to log in with the same static password.
        """,
    )

    # login_html = Unicode()

    def authenticate(self, request):
        """Checks against a global password if it's been set. If not, allow any user/pass combo"""
        if self.password:
            if request.form["password"] == self.password:
                namespace = request.form["username"]
            else:
                return None
        namespace = request.form["username"]

        return schema.AuthenticationToken(
            primary_namespace=namespace,
            role_bindings={
                "*/*": ["admin"],
            },
        )


class GenericOAuthAuthentication(Authentication):
    """ """

    access_token_url = Unicode(
        "https://github.com/login/oauth/access_token", config=True, help=""
    )
    authorize_url = Unicode(
        "https://github.com/login/oauth/authorize", config=True, help=""
    )
    client_id = Unicode("", config=True, help="")
    client_secret = Unicode("", config=True, help="")
    access_scope = Unicode("user:email", config=True, help="")
    user_data_url = Unicode(
        "https://api.github.com/user",
        config=True,
        help="API endpoint for OAuth provider that returns a JSON dict with user data",
    )

    login_html = Unicode(
        """
<div class="text-center">
    <form class="form-signin" method="POST">
        <h1 class="h3 mb-3 fw-normal">Please sign in via OAuth</h1>
        <button class="w-100 btn btn-lg btn-primary" type="submit">{SIGN_IN_BUTTON_TEXT}</button>
    </form>
</div>
        """,
        help="html form to use for login",
        config=True,
    )

    sign_in_button_text = Unicode(
        "Sign in with GitHub",
        config=True,
        help="Text that will be displayed in the Sign In button.",
    )

    @staticmethod
    def oauth_route(auth_url, client_id, redirect_uri, scope=None):
        return f"{auth_url}?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scope}"

    def routes(self):
        return super().routes + [
            ("/oauth_callback/", "GET", self.get_oauth_callback_method),
            ("/user/", "GET", self.get_oauth_user_method),
        ]

    def authenticate(self, request):
        response = self.redirect_oauth_provider()

        # poll until we get a token ?? 60s total
        waiting_times = 1, 1, 1, 1, 1, 5, 5, 5, 5, 5, 10, 10, 10
        for wait in waiting_times:
            access_token = session.get("access_token")
            if access_token:
                del session["access_token"]
                # return access_token  # shouldn't we keep the GH token somewhere?
                return schema.AuthenticationToken(
                    primary_namespace="default",
                    role_bindings={
                        "*/*": ["admin"],
                    },
                )

            sleep(wait)

    def redirect_oauth_provider(self):
        return redirect(
            self.oauth_route(
                auth_url=self.authorize_url,
                client_id=self.client_id,
                redirect_uri=url_for("/oauth_callback", _external=True),
                scope=self.access_scope,
            )
        )

    def get_oauth_callback_method(self):
        code = request.args.get("code")
        response = requests.post(
            self.access_token_url,
            json={
                "code": code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "authorization_code",
                "redirect_uri": url_for("/oauth_callback", _external=True),
                "scope": self.access_scope,
            },
        )
        response.raise_for_status()
        session["access_token"] = response.json()["access_token"]

    def get_oauth_user_method():
        pass


class DanceOAuthAuthentication(Authentication):
    """ """

    login_html = Unicode(
        """
<div class="text-center">
    <h1 class="h3 mb-3 fw-normal">Please sign in via OAuth</h1>
    <a class="w-100 btn btn-lg btn-primary" href="/oauth_login">{SIGN_IN_BUTTON_TEXT}</a>
</div>
        """,
        help="html form to use for login",
        config=True,
    )

    sign_in_button_text = Unicode(
        "Sign in with GitHub",
        config=True,
        help="Text that will be displayed in the Sign In button.",
    )

    flask_dance_oauth_provider = Unicode(
        "github",
        config=True,
        help="OAuth provider. Any module under `flask_dance.contrib`.",
    )

    secret_key = Unicode(
        "super_secret_key",
        config=True,
        help="A secret key needed for some authentication methods.",
    )

    oauth_client_id = Unicode(
        "", config=True, help="Identifier for the OAuth client chosen"
    )
    oauth_client_secret = Unicode(
        "", config=True, help="Secret token for the OAuth client chosen"
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app.secret_key = self.secret_key
        self.app.config["GITHUB_OAUTH_CLIENT_ID"] = self.oauth_client_id
        self.app.config["GITHUB_OAUTH_CLIENT_SECRET"] = self.oauth_client_secret

        provider_str = self.flask_dance_oauth_provider
        self.oauth_provider = import_string(
            f"flask_dance.contrib.{provider_str}.{provider_str}"
        )
        self.oauth_blueprint_factory = import_string(
            f"flask_dance.contrib.{provider_str}.make_{provider_str}_blueprint"
        )
        self.app.register_blueprint(
            self.oauth_blueprint_factory(), url_prefix="/oauth_login"
        )
