import enum
import re
import secrets
import datetime

import jwt
from traitlets.config import LoggingConfigurable
from traitlets import Dict, Unicode, Type
from flask import response, request, make_response

from conda_store_server import schema


ARN_ALLOWED_REGEX = re.compile(r'[A-Za-z\_\-\*]+/[A-Za-z\_\-\*]+')


class Permissions(enum.Enum):
    ENVIRONMENT_CREATE = "build::create"
    ENVIRONMENT_READ = "build::read"
    ENVIRONMENT_UPDATE = "build::update"
    ENVIRONMENT_DELETE = "build::delete"


class AuthenticationBackend(LoggingConfigurable):
    secret = Unicode(
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

    def encrypt_token(self, token : schema.AuthenticationToken):
        return jwt.encode(token.dict(), self.secret, algorithm=self.jwt_algorithm)

    def decrypt_token(self, token : str):
        return jwt.decode(token, self.secret, algorithms=[self.jwt_algorithm])

    def authenticate(self, token):
        try:
            return schema.AuthenticationToken.parse_obj(self.decrypt_token(token))
        except:
            return None


class RBACAuthorizationBackend(LoggingConfigurable):
    role_mappings = Dict(
        {
            'viewer': {Permissions.ENVIRONMENT_READ},
            'developer': {
                Permissions.ENVIRONMENT_CREATE,
                Permissions.ENVIRONMENT_READ,
                Permissions.ENVIRONMENT_DELETE,
            },
            'admin': {
                Permissions.ENVIRONMENT_CREATE,
                Permissions.ENVIRONMENT_READ,
                Permissions.ENVIRONMENT_UPDATE,
                Permissions.ENVIRONMENT_DELETE,
            }
        },
        help="default role to permissions mapping to use",
        config=True,
    )

    unauthenticated_role_bindings = Dict(
        {},
        help='default roles bindings to asign to unauthenticated users',
        config=True,
    )

    authenticated_role_bindings = Dict(
        {
            'default/*': {'viewer'},
            'filesystem/*': {'viewer'},
        },
        help='default permissions to apply to specific resources'
    )

    @staticmethod
    def compile_arn(arn):
        """Take an arn of form "example-*/example-*" and compile to regular expression

        """
        if not ARN_ALLOWED_REGEX.match(arn):
            raise ValueError(f'invalid arn={arn}')

        regex_arn = '^' + re.sub(r'\*', r'[A-Za-z_\-]*', arn) + '$'
        return re.compile(regex_arn)

    def entity_roles(self, arn, entity_bindings, authenticated=False):
        if authenticated:
            entity_bindings = {**self.authenticated_role_bindings, **entity_bindings}
        else:
            entity_bindings = {**self.unauthenticated_role_bindings, **entity_bindings}

        roles = set()
        for entity_arn, entity_roles in entity_bindings.items():
            if self.compile_arn(entity_arn).match(arn):
                roles = roles | set(entity_roles)
        return roles

    def convert_roles_to_permissions(self, roles):
        permissions = set()
        for role in roles:
            permissions = permissions | self.role_mappings[role]
        return permissions

    def authorized(self, entity_bindings, arn, permissions, authenticated=False):
        roles = self.entity_roles(arn, entity_bindings, authenticated=False)
        return permissions <= self.convert_roles_to_permissions(roles)


class Authentication(LoggingConfigurable):
    cookie_name = Unicode(
        'conda-store-auth',
        help="name of cookie used for authentication",
        config=True,
    )

    authentication_backend = Type(
        AuthenticationBackend,
        help='class for authentication implementation',
        config=True
    )

    authorization_backend = Type(
        AuthorizationBackend,
        help='clas for authorization implementation',
        config=True,
    )

    @property
    def authentication(self):
        if hasattr(self, '_authentication'):
            return self._authentication
        self._authentication = self.authentication_backend(parent=self, log=self.log)
        return self._authentication

    @property
    def authorization(self):
        if hasattr(self, '_authorization'):
            return self._authorization
        self._authorization = self.authorization_backend(parent=self, log=self.log)
        return self._authorization

    @property
    def routes(self):
        return [
            ('/login/', 'GET', self.get_login_method),
            ('/login/', 'POST', self.post_login_method),
            ('/logout/', 'POST', self.post_logout_method),
        ]

    def authenticate(self, request):
        return AuthenticationToken(
            primary_namespace="default",
            role_bindings={
                '*/*': ['admin'],
            }
        )

    def get_login_method(self):
        return render_template('login.html')

    def post_login_method(self):
        redirect_url = request.args.get('next', '/')
        response = redirect(redirect_url)
        authentication_token = self.authenticate(request)
        if authentication_token is None:
            return make_response(
                jsonify({'status': 'error', 'message': 'invalid authentication'}),
                403)

        response.set_cookie(
            self.cookie_name,
            self.authentication.encrypt_token(authentication_token),
            http_only=True,
            samesite='strict',
            # set cookie to expire at same time as jwt
            max_age=(authentication_token.exp - datetime.datetime.utcnow()).seconds,
        )
        return response

    def post_logout_method(self):
        redirect_url = request.args.get('next', '/')
        response = redirect(redirect_url)
        response.set_cookie(self.cookie_name, '', expires=0)
        return response
