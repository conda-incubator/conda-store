from conda_store_server.server.app import CondaStoreServer

main = CondaStoreServer.launch_instance

if __name__ == "__main__":
    main()
