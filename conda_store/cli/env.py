import yaml

from conda_store import client


def initialize_env_cli(subparser):
    parser = subparser.add_parser("env", help="manage conda environments")
    parser.add_argument(
        "action",
        choices=["create", "list"],
        help="action to take on conda environments",
    )
    parser.add_argument("-f", "--filename", help="conda environment filename to use")
    parser.set_defaults(func=handle_environment)


def handle_environment(args):
    if args.action == "list":
        data = client.get_environments()
        print("{:10}{:32}{:32}".format("BUILD", "NAME", "SHA256"))
        print("=" * 74)
        for row in data:
            name = row["name"]
            build_id = row["build_id"]
            sha256 = row.get("specification", {}).get("sha256")
            print(f"{build_id:<10}{name:32}{sha256[:32]:32}")

    elif args.action == "create":
        with open(args.filename) as f:
            data = yaml.safe_load(f)
        client.post_specification(data)
