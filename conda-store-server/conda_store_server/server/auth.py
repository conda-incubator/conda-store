import base64
import datetime
import re
import secrets
from collections import defaultdict
from typing import Optional

import jwt
import requests
import yarl
from conda_store_server import api, orm, schema, utils
from conda_store_server.server import dependencies
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy import and_, or_, text
from sqlalchemy.orm import sessionmaker
from traitlets import (
    Bool,
    Callable,
    Dict,
    Instance,
    Integer,
    TraitError,
    Type,
    Unicode,
    Union,
    default,
    validate,
)
from traitlets.config import LoggingConfigurable

ARN_ALLOWED_REGEX = re.compile(schema.ARN_ALLOWED)


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

    predefined_tokens = Dict(
        {},
        help="Set of tokens with predefined permissions. The feature is helpful for service-accounts",
        config=True,
    )

    def encrypt_token(self, token: schema.AuthenticationToken):
        return jwt.encode(token.dict(), self.secret, algorithm=self.jwt_algorithm)

    def decrypt_token(self, token: str):
        return jwt.decode(token, self.secret, algorithms=[self.jwt_algorithm])

    def authenticate(self, token):
        try:
            if token in self.predefined_tokens:
                authentication_token = self.predefined_tokens[token]
            else:
                authentication_token = self.decrypt_token(token)
            return schema.AuthenticationToken.parse_obj(authentication_token)
        except Exception:
            return None


class RBACAuthorizationBackend(LoggingConfigurable):
    role_mappings_version = Integer(
        1,
        help="Role mappings version to use: 1 (default, legacy), 2 (new, recommended)",
        config=True,
    )

    def _database_role_bindings_v1(self, entity: schema.AuthenticationToken):
        with self.authentication_db() as db:
            result = db.execute(
                text(
                    """
                    SELECT nrm.entity, nrm.role
                    FROM namespace n
                    RIGHT JOIN namespace_role_mapping nrm ON nrm.namespace_id = n.id
                    WHERE n.name = :primary_namespace
                    """
                ),
                {"primary_namespace": entity.primary_namespace},
            )
            raw_role_mappings = result.mappings().all()

            db_role_mappings = defaultdict(set)
            for row in raw_role_mappings:
                db_role_mappings[row["entity"]].add(row["role"])

        return db_role_mappings

    def _database_role_bindings_v2(self, entity: schema.AuthenticationToken):
        def _convert_namespace_to_entity_arn(namespace):
            return f"{namespace}/*"

        with self.authentication_db() as db:
            # Must have the same format as authenticated_role_bindings:
            # {
            #     "default/*": {"viewer"},
            #     "filesystem/*": {"viewer"},
            # }
            res = defaultdict(set)

            # FIXME: Remove try-except.
            # Used in tests to check default permissions without populating the
            # DB, which raises an exception since namespace is not found.
            try:
                roles = api.get_other_namespace_roles(db, name=entity.primary_namespace)
            except Exception:
                return res

            for x in roles:
                res[_convert_namespace_to_entity_arn(x.namespace)].add(x.role)
            return res

    # version -> DB bindings
    _role_mappings_versions = {
        1: _database_role_bindings_v1,
        2: _database_role_bindings_v2,
    }

    @validate("role_mappings_version")
    def _check_role_mappings_version(self, proposal):
        expected = tuple(self._role_mappings_versions.keys())
        if proposal.value not in expected:
            raise TraitError(
                f"c.RBACAuthorizationBackend.role_mappings_version: "
                f"invalid role mappings version: {proposal.value}, "
                f"expected: {expected}"
            )
        return proposal.value

    _viewer_permissions = {
        schema.Permissions.ENVIRONMENT_READ,
        schema.Permissions.NAMESPACE_READ,
        schema.Permissions.NAMESPACE_ROLE_MAPPING_READ,
    }
    _editor_permissions = {
        schema.Permissions.BUILD_CANCEL,
        schema.Permissions.ENVIRONMENT_CREATE,
        schema.Permissions.ENVIRONMENT_READ,
        schema.Permissions.ENVIRONMENT_UPDATE,
        schema.Permissions.ENVIRONMENT_SOLVE,
        schema.Permissions.NAMESPACE_READ,
        schema.Permissions.NAMESPACE_ROLE_MAPPING_READ,
        schema.Permissions.SETTING_READ,
    }
    _admin_permissions = {
        schema.Permissions.BUILD_DELETE,
        schema.Permissions.BUILD_CANCEL,
        schema.Permissions.ENVIRONMENT_CREATE,
        schema.Permissions.ENVIRONMENT_DELETE,
        schema.Permissions.ENVIRONMENT_READ,
        schema.Permissions.ENVIRONMENT_UPDATE,
        schema.Permissions.ENVIRONMENT_SOLVE,
        schema.Permissions.NAMESPACE_CREATE,
        schema.Permissions.NAMESPACE_DELETE,
        schema.Permissions.NAMESPACE_READ,
        schema.Permissions.NAMESPACE_UPDATE,
        schema.Permissions.NAMESPACE_ROLE_MAPPING_CREATE,
        schema.Permissions.NAMESPACE_ROLE_MAPPING_READ,
        schema.Permissions.NAMESPACE_ROLE_MAPPING_UPDATE,
        schema.Permissions.NAMESPACE_ROLE_MAPPING_DELETE,
        schema.Permissions.SETTING_READ,
        schema.Permissions.SETTING_UPDATE,
    }

    role_mappings = Dict(
        {
            "viewer": _viewer_permissions,
            "editor": _editor_permissions,
            "admin": _admin_permissions,
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
        config=True,
    )

    authentication_db = Instance(
        sessionmaker,
        help="SQLAlchemy session to query DB. Used for role mapping",
        config=False,
    )

    @staticmethod
    def compile_arn_regex(arn: str) -> re.Pattern:
        """Take an arn of form "example-*/example-*" and compile to regular expression

        The expression "example-*/example-*" will match:
          - "example-asdf"
          - "example-asdf/example-qwer"
        """
        if not ARN_ALLOWED_REGEX.match(arn):
            raise ValueError(f"invalid arn={arn}")

        # replace "*" with schema.ALLOWED_CHARACTERS
        arn = re.sub(r"\*", f"[{schema.ALLOWED_CHARACTERS}]*", arn)
        namespace_regex, name_regex = arn.split("/")
        regex_arn = "^" + namespace_regex + "(?:/" + name_regex + ")?$"
        return re.compile(regex_arn)

    @staticmethod
    def compile_arn_sql_like(arn: str) -> str:
        match = ARN_ALLOWED_REGEX.match(arn)
        if match is None:
            raise ValueError(f"invalid arn={arn}")

        return re.sub(r"\*", "%", match.group(1)), re.sub(r"\*", "%", match.group(2))

    @staticmethod
    def is_arn_subset(arn_1: str, arn_2: str):
        """Return true if arn_1 is a subset of arn_2

        conda-store allows flexible arn statements such as "a*b*/c*"
        with "*" being a wildcard seen in regexes. This makes the
        calculation of if a arn is a subset of another non
        trivial. This codes solves this problem.
        """
        arn_1_matches_arn_2 = (
            re.fullmatch(
                re.sub(r"\*", f"[{schema.ALLOWED_CHARACTERS}*]*", arn_1), arn_2
            )
            is not None
        )
        arn_2_matches_arn_1 = (
            re.fullmatch(
                re.sub(r"\*", f"[{schema.ALLOWED_CHARACTERS}*]*", arn_2), arn_1
            )
            is not None
        )
        return (arn_1_matches_arn_2 and arn_2_matches_arn_1) or arn_2_matches_arn_1

    def get_entity_bindings(self, entity: schema.AuthenticationToken):
        authenticated = entity is not None
        entity_role_bindings = {} if entity is None else entity.role_bindings

        if authenticated:
            db_role_bindings = self.database_role_bindings(entity)

            return {
                **self.authenticated_role_bindings,
                **entity_role_bindings,
                **db_role_bindings,
            }
        else:
            return {
                **self.unauthenticated_role_bindings,
                **entity_role_bindings,
            }

    def convert_roles_to_permissions(self, roles):
        permissions = set()
        for role in roles:
            # 'editor' is the new alias of 'developer'. The new name is
            # preferred in user-visible settings (like 'role_mappings') and when
            # calling the role-mappings HTTP APIs, but it's ALWAYS mapped to
            # 'developer' in the database for compatibility reasons.
            # Additionally, this code allows for legacy 'role_mappings' that
            # used to specify the role as 'developer'. Because it's a
            # user-visible setting, we cannot break compatibility here
            if role == "editor":
                raise ValueError("role must never be 'editor' in the database")
            if role == "developer":
                # Checks the new user-visible name first, then tries the legacy
                # one. This will raise an exception if both keys are not found
                role_mappings = (
                    self.role_mappings.get("editor") or self.role_mappings["developer"]
                )
            else:
                role_mappings = self.role_mappings[role]
            permissions = permissions | role_mappings
        return permissions

    def get_entity_binding_permissions(self, entity: schema.AuthenticationToken):
        entity_bindings = self.get_entity_bindings(entity)
        return {
            entity_arn: self.convert_roles_to_permissions(roles=entity_roles)
            for entity_arn, entity_roles in entity_bindings.items()
        }

    def get_entity_permissions(self, entity: schema.AuthenticationToken, arn: str):
        """Get set of permissions for given ARN given AUTHENTICATION
        state and entity_bindings

        ARN is a specific "<namespace>/<name>"
        AUTHENTICATION is either True/False
        ENTITY_BINDINGS is a mapping of ARN with regex support to ROLES
        ROLES is a set of roles defined in `RBACAuthorizationBackend.role_mappings`
        """
        entity_binding_permissions = self.get_entity_binding_permissions(entity)
        permissions = set()
        for entity_arn, entity_permissions in entity_binding_permissions.items():
            if self.compile_arn_regex(entity_arn).match(arn):
                permissions = permissions | set(entity_permissions)
        return permissions

    def is_subset_entity_permissions(self, entity, new_entity):
        """Determine if new_entity_bindings is a strict subset of entity_bindings

        This feature is required to allow authenticated entitys to
        create new permissions that are a strict subset of its
        permissions.
        """
        entity_binding_permissions = self.get_entity_binding_permissions(entity)
        new_entity_binding_permissions = self.get_entity_binding_permissions(new_entity)
        for (
            new_entity_binding,
            new_permissions,
        ) in new_entity_binding_permissions.items():
            _permissions = set()
            for entity_binding, permissions in entity_binding_permissions.items():
                if self.is_arn_subset(new_entity_binding, entity_binding):
                    _permissions = _permissions | permissions

            if not new_permissions <= _permissions:
                return False
        return True

    def authorize(
        self, entity: schema.AuthenticationToken, arn: str, required_permissions
    ):
        return required_permissions <= self.get_entity_permissions(
            entity=entity, arn=arn
        )

    def database_role_bindings(self, entity: schema.AuthenticationToken):
        # This method can be reached from the router_ui via filter_environments.
        # Since the UI routes are not versioned, we don't know which API version
        # the client might be using. So we rely on the role_mappings_version
        # config option to access the proper DB table.
        return self._role_mappings_versions.get(self.role_mappings_version)(
            self, entity
        )


class Authentication(LoggingConfigurable):
    cookie_name = Unicode(
        "conda-store-auth",
        help="name of cookie used for authentication",
        config=True,
    )

    cookie_domain = Unicode(
        None,
        help="Use when wanting to set a subdomain wide cookie. For example setting this to `example.com` would allow the cookie to be valid for `example.com` along with `*.example.com`.",
        allow_none=True,
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

    authentication_db = Instance(
        sessionmaker,
        help="SQLAlchemy session to query DB. Used for role mapping",
        config=False,
    )

    @property
    def router(self):
        router = APIRouter(tags=["auth"])
        for path, method, func in self.routes:
            getattr(router, method)(path, name=func.__name__)(func)
        return router

    login_html = Unicode(
        """
<div class="text-center">
    <form class="form-signin" id="login">
        <h1 class="h3 mb-3 fw-normal">Please sign in</h1>
        <div class="form-floating">
            <input name="username" class="form-control" id="username" placeholder="Username">
            <label for="floatingInput">Username</label>
        </div>
        <div class="form-floating">
            <input name="password" type="password" class="form-control" id="password" placeholder="Password">
            <label for="floatingPassword">Password</label>
        </div>
        <button class="w-100 btn btn-lg btn-primary" type="submit">Sign In</button>
    </form>
</div>

<script>
function bannerMessage(message) {
    let banner = document.querySelector('#message');
    banner.innerHTML = message;
}

async function loginHandler(event) {
    event.preventDefault();

    usernameInput = document.querySelector("input#username");
    passwordInput = document.querySelector("input#password");

    let response = await fetch("{{ url_for('post_login_method') }}", {
        method: "POST",
        body: JSON.stringify({
            username: usernameInput.value,
            password: passwordInput.value,
        }),
        headers: {'Content-Type': "application/json"},
    });

    let data = await response.json();

    if (response.ok) {
        window.location = data.data.redirect_url;
    } else {
        bannerMessage(`<div class="alert alert-danger col">${data.message}</div>`);
    }
}

let form = document.querySelector("form#login")
form.addEventListener('submit', loginHandler);
</script>
        """,
        help="html form to use for login",
        config=True,
    )

    def get_login_html(self, request: Request, templates):
        return templates.env.from_string(self.login_html).render(request=request)

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
        self._authorization = self.authorization_backend(
            parent=self, log=self.log, authentication_db=self.authentication_db
        )
        return self._authorization

    @property
    def routes(self):
        return [
            ("/login/", "get", self.get_login_method),
            ("/login/", "post", self.post_login_method),
            ("/logout/", "post", self.post_logout_method),
        ]

    async def authenticate(self, request: Request):
        return schema.AuthenticationToken(
            primary_namespace="default",
            role_bindings={
                "*/*": ["admin"],
            },
        )

    def get_login_method(
        self,
        request: Request,
        next: Optional[str] = None,
        templates=Depends(dependencies.get_templates),
    ):
        request.session["next"] = next
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "login_html": self.get_login_html(request, templates)},
        )

    async def _post_login_method_response(self, redirect_url: str):
        return JSONResponse(
            content=jsonable_encoder(
                {
                    "status": "ok",
                    "data": {"redirect_url": redirect_url},
                }
            )
        )

    async def post_login_method(
        self,
        request: Request,
        response: Response,
        next: Optional[str] = None,
        templates=Depends(dependencies.get_templates),
    ):
        authentication_token = await self.authenticate(request)
        if authentication_token is None:
            raise HTTPException(
                status_code=403, detail="Invalid authentication credentials"
            )

        request.session["next"] = next or request.session.get("next")
        redirect_url = request.session.pop("next") or str(
            request.url_for("ui_list_environments")
        )
        response = await self._post_login_method_response(redirect_url)
        response.set_cookie(
            self.cookie_name,
            self.authentication.encrypt_token(authentication_token),
            httponly=True,
            samesite="strict",
            domain=self.cookie_domain,
            # set cookie to expire at same time as jwt
            max_age=int(
                (authentication_token.exp - datetime.datetime.utcnow()).total_seconds()
            ),
        )
        return response

    def post_logout_method(self, request: Request, next: Optional[str] = None):
        redirect_url = next or request.url_for("ui_list_environments")
        response = RedirectResponse(redirect_url, status_code=303)
        response.set_cookie(self.cookie_name, "", domain=self.cookie_domain, expires=0)
        return response

    def authenticate_request(self, request: Request, require=False):
        if hasattr(request.state, "entity"):
            pass  # only authenticate once
        elif request.cookies.get(self.cookie_name):
            # cookie based authentication
            token = request.cookies.get(self.cookie_name)
            request.state.entity = self.authentication.authenticate(token)
        elif "Authorization" in request.headers:
            parts = request.headers["Authorization"].split(" ", 1)
            if parts[0].lower() == "basic":
                try:
                    username, token = base64.b64decode(parts[1]).decode().split(":", 1)
                    request.state.entity = self.authentication.authenticate(token)
                except Exception:
                    pass
            elif parts[0].lower() == "bearer":
                request.state.entity = self.authentication.authenticate(parts[1])
            else:
                request.state.entity = None
        else:
            request.state.entity = None

        if require and request.state.entity is None:
            raise HTTPException(
                status_code=401,
                detail="request not authenticated",
            )
        return request.state.entity

    def entity_bindings(self, entity):
        return self.authorization.get_entity_bindings(entity)

    def authorize_request(self, request: Request, arn, permissions, require=False):
        if not hasattr(request.state, "entity"):
            self.authenticate_request(request)

        if not hasattr(request.state, "authorized"):
            request.state.authorized = self.authorization.authorize(
                request.state.entity, arn, permissions
            )

        if require and not request.state.authorized:
            raise HTTPException(
                status_code=403,
                detail="request not authorized",
            )

        return request.state.authorized

    def filter_builds(self, entity, query):
        cases = []
        for entity_arn, entity_roles in self.entity_bindings(entity).items():
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

    def filter_environments(self, entity, query):
        cases = []
        for entity_arn, entity_roles in self.entity_bindings(entity).items():
            namespace, name = self.authorization.compile_arn_sql_like(entity_arn)
            cases.append(
                and_(
                    orm.Namespace.name.like(namespace), orm.Environment.name.like(name)
                )
            )

        if not cases:
            return query.filter(False)

        return query.join(orm.Environment.namespace).filter(or_(*cases))

    def filter_namespaces(self, entity, query):
        cases = []
        for entity_arn, entity_roles in self.entity_bindings(entity).items():
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

    async def authenticate(self, request: Request):
        """Checks against a global password if it's been set. If not, allow any user/pass combo"""
        data = await request.json()
        if self.password and data.get("password") != self.password:
            return None

        return schema.AuthenticationToken(
            primary_namespace=data["username"],
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

    oauth_callback_url = Union(
        [Unicode(), Callable()],
        config=True,
        help="Callback URL to use. Typically `{protocol}://{host}/{prefix}/oauth_callback`",
    )

    @default("oauth_callback_url")
    def _default_oauth_callback_url(self):
        def _oauth_callback_url(request: Request):
            return request.url_for("post_login_method")

        return _oauth_callback_url

    def get_oauth_callback_url(self, request: Request):
        return utils.callable_or_value(self.oauth_callback_url, request)

    def get_login_method(
        self,
        request: Request,
        next: Optional[str] = None,
        templates=Depends(dependencies.get_templates),
    ):
        request.session["next"] = next

        state = secrets.token_urlsafe()
        request.session["oauth_state"] = state
        authorization_url = self.oauth_route(
            auth_url=self.authorize_url,
            client_id=self.client_id,
            redirect_uri=self.get_oauth_callback_url(request),
            scope=self.access_scope,
            state=state,
        )
        return RedirectResponse(authorization_url)

    @staticmethod
    def oauth_route(auth_url, client_id, redirect_uri, scope=None, state=None):
        url = yarl.URL(auth_url) % {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
        }

        if scope is not None:
            url = url % {"scope": scope}
        if state is not None:
            url = url % {"state": state}
        return str(url)

    async def _post_login_method_response(self, redirect_url):
        return HTMLResponse(
            content=f"""
<script>
  window.location = "{redirect_url}";
</script>
        """,
            status_code=200,
        )

    @property
    def routes(self):
        return [
            ("/login/", "get", self.get_login_method),
            ("/logout/", "post", self.post_logout_method),
            ("/oauth_callback/", "get", self.post_login_method),
        ]

    async def authenticate(self, request: Request):
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

    def _get_oauth_token(self, request: Request):
        # 1. Get callback URI params, which include `code` and `state`
        #    `code` will be used to request the token; `state` must match our session's!
        code = request.query_params.get("code")
        state = request.query_params.get("state")
        if request.session["oauth_state"] != state:
            raise HTTPException(status_code=401, detail="OAuth states do not match")
        del request.session["oauth_state"]

        # 2. Request actual access token with code and secret
        r_response = requests.post(
            self.access_token_url,
            data={
                "code": code,
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.get_oauth_callback_url(request),
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
            headers={"Authorization": f"Bearer {authentication_token}"},
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
