import enum
import re

from traitlets.config import LoggingConfigurable
from traitlets import Dict


ARN_ALLOWED_REGEX = re.compile('[A-Za-z\_\-\*]+/[A-Za-z\_\-\*]+')


class Permissions(enum.Enum):
    ENVIRONMENT_CREATE = "build::create"
    ENVIRONMENT_READ = "build::read"
    ENVIRONMENT_UPDATE = "build::update"
    ENVIRONMENT_DELETE = "build::delete"


class RBACAuthorization(LoggingConfigurable):
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
            'default/*': 'viewer',
            'filesystem/*': 'viewer',
        },
        help='default permissions to apply to specific resources'
    )

    @staticmethod
    def compile_arn(arn):
        """Take an arn of form "example-*/example-*" and compile to regular expression

        """
        if not ARN_ALLOWED_REGEX.match(arn):
            raise ValueError(f'invalid arn={arn}')

        regex_arn = '^' + re.sub('\*', '[A-Za-z_\-]*', arn) + '$'
        return re.compile(regex_arn)

    def entity_roles(self, arn, entity_bindings, authenticated=False):
        roles = set()

        if authenticated:
            entity_bindings = {**self.authenticated_role_bindings, **entity_bindings}
        else:
            entity_bindings = {**self.unauthenticated_role_bindings, **entity_bindings}

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
