from conda_store_server.worker.app import CondaStoreWorker

main = CondaStoreWorker.launch_instance

if __name__ == "__main__":
    main()
