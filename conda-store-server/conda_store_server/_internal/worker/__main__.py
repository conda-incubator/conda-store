from conda_store_server._internal.worker.app import CondaStoreWorker


main = CondaStoreWorker.launch_instance

if __name__ == "__main__":
    main()
