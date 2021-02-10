from conda_store.server import start_app


def initialize_server_cli(subparser):
    parser = subparser.add_parser(
        "serve", help="serve ui, api, and registry for conda build"
    )
    parser.add_argument(
        "--address",
        type=str,
        default="0.0.0.0",
        help="address to bind run conda-store ui",
    )
    parser.add_argument(
        "--port", type=int, default=5000, help="port to run conda-store ui"
    )
    parser.add_argument(
        "-s",
        "--store",
        type=str,
        default=".conda-store",
        help="directory for conda-store state",
    )
    parser.add_argument(
        "--storage-backend",
        type=str,
        default="s3",
        choices=["filesystem", "s3"],
        help="backend for storing build artifacts. Production should use s3",
    )
    parser.add_argument(
        "--disable-ui", action="store_true", help="disable ui for conda store"
    )
    parser.add_argument(
        "--disable-api", action="store_true", help="disable api for conda store"
    )
    parser.add_argument(
        "--disable-registry",
        action="store_true",
        help="disable docker registry for conda store",
    )
    parser.add_argument("--verbose", action="store_true", help="enable debug logging")
    parser.set_defaults(func=handle_ui)


def handle_ui(args):
    start_app(
        args.store,
        args.storage_backend,
        disable_ui=args.disable_ui,
        disable_api=args.disable_api,
        disable_registry=args.disable_registry,
        address=args.address,
        port=args.port,
    )
