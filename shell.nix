let
  pkgs = import <nixpkgs> {};

  pythonPackages = pkgs.python3Packages;
in
pkgs.mkShell {
  buildInputs = [
    pkgs.yarn
    pkgs.docker-compose

    pythonPackages.pyyaml
    pythonPackages.flask
    pythonPackages.requests
    pythonPackages.minio
    pythonPackages.sqlalchemy
    pythonPackages.minio
    pythonPackages.pydantic

    pythonPackages.pytest
    pythonPackages.pytest-mock
    pythonPackages.black
    pythonPackages.flake8
  ];

  shellHook = ''
    export PATH="$PWD/node_modules/.bin/:$PATH"
  '';
}
