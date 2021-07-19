def create_worker():
    from conda_store_server.worker.app import CondaStoreWorker

    worker = CondaStoreWorker()
    worker.initialize()
    return worker
