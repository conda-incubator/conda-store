import typing

from conda_store_server import schema, api


def initialize_database(
    db, config: typing.Dict[str, typing.Dict[str, schema.CondaSpecification]]
):
    for namespace_name in config:
        namespace = api.ensure_namespace(db, name=namespace_name)
        for environment_name, specification in config[namespace_name].items():
            environment = api.ensure_environment(
                db,
                name=specification.name,
                namespace_id=namespace.id,
            )
            specification = api.ensure_specification(db, specification)
            api.create_build(db, environment.id, specification.id)
            api.create_solve(db, specification.id)
            db.commit()
