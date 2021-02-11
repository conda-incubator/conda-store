let
  pkgs = import <nixpkgs> {};

  pythonPackages = pkgs.python3Packages;
in
pkgs.mkShell {
  buildInputs = [
    pkgs.yarn
    pkgs.docker-compose
    pkgs.kubectl
    pkgs.minikube
    pkgs.kompose

    pythonPackages.pyyaml
    pythonPackages.flask
    pythonPackages.flask-cors
    pythonPackages.requests
    pythonPackages.minio
    pythonPackages.sqlalchemy
    pythonPackages.minio
    pythonPackages.pydantic

    pythonPackages.pytest
    pythonPackages.pytest-mock
    pythonPackages.black
    pythonPackages.flake8
    pythonPackages.sphinx
    pythonPackages.recommonmark
    pythonPackages.sphinx_rtd_theme
  ];

  shellHook = ''
    export PATH="$PWD/node_modules/.bin/:$PATH"
  '';
}
