from uuid import uuid4
from conda_store_server import api
from conda_store_server._internal import schema
from conda_store_server._internal.worker import tasks


# def test_memory_leak(testclient):
def test_memory_leak(db, conda_store, celery_worker):
    # DIDNT WORK
    # conda_store.celery_app
    
    # @conda_store.celery_app.task(name='return_memory')
    # def return_memory():
    #     return "4GiB"
    
    # breakpoint()
    # # conda_store.celery_app.register_task(return_memory)
    # result = return_memory.apply_async()
    # real_result = result.get()
    # print(f'REAL RESULT = {real_result}')
    conda_specification = schema.CondaSpecification(
        name=f"pytest-{uuid4()}",
        channels=["conda-forge"],
        dependencies=["python"],
    )
    namespace_name = "default"

    build_id = conda_store.register_environment(
        db, specification=conda_specification.dict(), namespace=namespace_name
    )
    
    build = api.get_build(db, build_id=build_id)
    assert build is not None
    assert build.status == schema.BuildStatus.QUEUED
    assert build.environment.name == conda_specification.name
    assert build.environment.namespace.name == namespace_name
    assert build.specification.spec["name"] == conda_specification.name
    assert build.specification.spec["channels"] == conda_specification.channels
    assert build.specification.spec["dependencies"] == conda_specification.dependencies
    # when new environment is created current_build should be the default build
    assert build.environment.current_build == build

    from celery.result import AsyncResult

    # wait for task to complete
    # build: environment, export, archive
    # docker is expected to fail will be fixed soon
    breakpoint()
    task = AsyncResult(f"build-{build.id}-environment")
    task.wait(timeout=1)


    print(f'build_id = {build_id}')
