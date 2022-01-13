import enum
import re
import secrets
import datetime

import jwt
import requests
from traitlets.config import LoggingConfigurable
from traitlets import Dict, Unicode, Type, default, Bool
from flask import (
    request,
    render_template,
    redirect,
    g,
    abort,
    jsonify,
    url_for,
    session,
)
from sqlalchemy import or_, and_

from conda_store_server import schema, orm


ARN_ALLOWED_REGEX = re.compile(
    r"^([A-Za-z0-9|<>=\.\_\-\*]+)/([A-Za-z0-9|<>=\.\_\-\*]+)$"
)


class Permissions(enum.Enum):
    ENVIRONMENT_CREATE = "environment:create"
    ENVIRONMENT_READ = "environment::read"
    ENVIRONMENT_UPDATE = "environment::update"
    ENVIRONMENT_DELETE = "environment::delete"
    BUILD_DELETE = "build::delete"
    NAMESPACE_CREATE = "namespace::create"
    NAMESPACE_READ = "namespace::read"
    NAMESPACE_DELETE = "namespace::delete"


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
            "viewer": {
                Permissions.ENVIRONMENT_READ,
                Permissions.NAMESPACE_READ,
            },
            "developer": {
                Permissions.ENVIRONMENT_CREATE,
                Permissions.ENVIRONMENT_READ,
                Permissions.ENVIRONMENT_UPDATE,
                Permissions.NAMESPACE_READ,
            },
            "admin": {
                Permissions.BUILD_DELETE,
                Permissions.ENVIRONMENT_CREATE,
                Permissions.ENVIRONMENT_DELETE,
                Permissions.ENVIRONMENT_READ,
                Permissions.ENVIRONMENT_UPDATE,
                Permissions.NAMESPACE_CREATE,
                Permissions.NAMESPACE_DELETE,
                Permissions.NAMESPACE_READ,
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
        """Take an arn of form "example-*/example-*" and compile to regular expression

        The expression "example-*/example-*" will match:
          - "example-asdf"
          - "example-asdf/example-qwer"
        """
        if not ARN_ALLOWED_REGEX.match(arn):
            raise ValueError(f"invalid arn={arn}")

        # replace "*" with "[A-Za-z0-9_\-\.|<>=]*"
        arn = re.sub(r"\*", r"[A-Za-z0-9_\-\.|<>=]*", arn)

        namespace_regex, name_regex = arn.split("/")
        regex_arn = "^" + namespace_regex + "(?:/" + name_regex + ")?$"
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
    <form class="form-signin" method="POST" id="login">
        <h1 class="h3 mb-3 fw-normal">Please sign in</h1>
        <div class="form-floating">
            <input name="username" class="form-control" id="floatingInput" placeholder="Username">
            <label for="floatingInput">Username</label>
        </div>
        <div class="form-floating">
            <input name="password" type="password" class="form-control" id="floatingPassword" placeholder="Password">
            <label for="floatingPassword">Password</label>
        </div>
        <button class="w-100 btn btn-lg btn-primary" type="submit">Sign In</button>
    </form>
</div>
        """,
        help="html form to use for login",
        config=True,
    )

    def get_login_html(self):
        return self.login_html

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
        return render_template("login.html", login_html=self.get_login_html())

    def post_login_method(self):
        redirect_url = request.args.get("next", url_for("ui.ui_get_user"))
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
                    orm.Environment.name.like(name),
                )
            )

        if not cases:
            return query.filter(False)

        return (
            query.join(orm.Build.environment)
            .join(orm.Environment.namespace)
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
        if self.password and request.form["password"] != self.password:
            return None

        return schema.AuthenticationToken(
            primary_namespace=request.form["username"],
            role_bindings={
                "*/*": ["admin"],
            },
        )


class GenericOAuthAuthentication(Authentication):
    """
    A provider-agnostic OAuth authentication provider. Configure endpoints, secrets and other
    parameters to enable any OAuth-compatible platform.
    """

    access_token_url = Unicode(
        config=True,
        help="URL used to request an access token once app has been authorized",
    )
    authorize_url = Unicode(
        config=True,
        help="URL used to request authorization to OAuth provider",
    )
    client_id = Unicode(
        config=True,
        help="Unique string that identifies the app against the OAuth provider",
    )
    client_secret = Unicode(
        config=True,
        help="Secret string used to authenticate the app against the OAuth provider",
    )
    access_scope = Unicode(
        config=True,
        help="Permissions that will be requested to OAuth provider.",
    )
    user_data_url = Unicode(
        config=True,
        help="API endpoint for OAuth provider that returns a JSON dict with user data",
    )
    user_data_key = Unicode(
        config=True,
        help="Key in the payload returned by `user_data_url` endpoint that provides the username",
    )

    tls_verify = Bool(
        True,
        config=True,
        help="Disable TLS verification on http request.",
    )

    oauth_callback_url = Unicode(
        config=True,
        help="Callback URL to use. Typically `{protocol}://{host}/{prefix}/oauth_callback`",
    )

    @default("oauth_callback_url")
    def _oauth_callback_url(self):
        return url_for("auth.post_login_method", _external=True)

    login_html = Unicode(
        """
<div id="login" class="text-center">
    <h1 class="h3 mb-3 fw-normal">Please sign in via OAuth</h1>
    <a class="w-100 btn btn-lg btn-primary" href="{authorization_url}">Sign in with OAuth</a>
</div>
        """,
        help="html form to use for login",
        config=True,
    )

    def get_login_html(self):
        state = secrets.token_urlsafe()
        session["oauth_state"] = state
        authorization_url = self.oauth_route(
            auth_url=self.authorize_url,
            client_id=self.client_id,
            redirect_uri=self.oauth_callback_url,
            scope=self.access_scope,
            state=state,
        )
        return self.login_html.format(authorization_url=authorization_url)

    @staticmethod
    def oauth_route(auth_url, client_id, redirect_uri, scope=None, state=None):
        r = f"{auth_url}?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code"
        if scope is not None:
            r += f"&scope={scope}"
        if state is not None:
            r += f"&state={state}"
        return r

    @property
    def routes(self):
        return [
            ("/login/", "GET", self.get_login_method),
            ("/logout/", "POST", self.post_logout_method),
            ("/oauth_callback/", "GET", self.post_login_method),
        ]

    def authenticate(self, request):
        # 1. using the callback_url code and state in request
        oauth_access_token = self._get_oauth_token(request)
        if oauth_access_token is None:
            return None  # authentication failed

        # 2. Who is the username? We need one more request
        username = self._get_username(oauth_access_token)

        # 3. create our own internal token
        return schema.AuthenticationToken(
            primary_namespace=username,
            role_bindings={
                "*/*": ["admin"],
            },
        )

    def _get_oauth_token(self, request):
        # 1. Get callback URI params, which include `code` and `state`
        #    `code` will be used to request the token; `state` must match our session's!
        code = request.args.get("code")
        state = request.args.get("state")
        if session["oauth_state"] != state:
            response = jsonify(
                {"status": "error", "message": "OAuth states do not match"}
            )
            response.status_code = 401
            abort(response)
        del session["oauth_state"]

        # 2. Request actual access token with code and secret
        r_response = requests.post(
            self.access_token_url,
            data={
                "code": code,
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            headers={"Accept": "application/json"},
            verify=self.tls_verify,
        )
        if r_response.status_code != 200:
            return None
        data = r_response.json()
        return data["access_token"]

    def _get_username(self, authentication_token):
        response = requests.get(
            self.user_data_url,
            headers={"Authorization": f"token {authentication_token}"},
            verify=self.tls_verify,
        )
        response.raise_for_status()
        return response.json()[self.user_data_key]


class GithubOAuthAuthentication(GenericOAuthAuthentication):
    github_url = Unicode("https://github.com", config=True)

    github_api = Unicode("https://api.github.com", config=True)

    @default("access_token_url")
    def _access_token_url_default(self):
        return "%s/login/oauth/access_token" % (self.github_url)

    @default("authorize_url")
    def _authorize_url_default(self):
        return "%s/login/oauth/authorize" % (self.github_url)

    @default("access_scope")
    def _access_scope_default(self):
        return "user:email"

    @default("user_data_url")
    def _user_data_url_default(self):
        return "%s/user" % (self.github_api)

    @default("user_data_key")
    def _user_data_key_default(self):
        return "login"

    @default("login_html")
    def _login_html_default(self):
        return """
<div id="login" class="text-center">
    <h1 class="h3 mb-3 fw-normal">Please sign in via OAuth</h1>
    <a class="w-100 btn btn-lg btn-primary" href="{authorization_url}">Sign in with GitHub</a>
</div>
        """


class JupyterHubOAuthAuthentication(GenericOAuthAuthentication):
    jupyterhub_url = Unicode(
        help="base url for jupyterhub not including the '/hub/'",
        config=True,
    )

    @default("access_token_url")
    def _access_token_url_default(self):
        return "%s/hub/api/oauth2/token" % (self.jupyterhub_url)

    @default("authorize_url")
    def _authorize_url_default(self):
        return "%s/hub/api/oauth2/authorize" % (self.jupyterhub_url)

    @default("access_scope")
    def _access_scope_default(self):
        return "profile"

    @default("user_data_url")
    def _user_data_url_default(self):
        return "%s/hub/api/user" % (self.jupyterhub_url)

    @default("user_data_key")
    def _user_data_key_default(self):
        return "name"

    @default("login_html")
    def _login_html_default(self):
        return """
<div id="login" class="text-center">
    <h1 class="h3 mb-3 fw-normal">Please sign in via OAuth</h1>
    <a class="w-100 btn btn-lg btn-primary" href="{authorization_url}">Sign in with JupyterHub</a>
</div>
        """
