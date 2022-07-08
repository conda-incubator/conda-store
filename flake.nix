{
  description = "conda-store";

  inputs = {
    nixpkgs = { url = "github:nixos/nixpkgs/nixpkgs-unstable"; };
  };

  outputs = inputs@{ self, nixpkgs, ... }: {
    devShell.x86_64-linux =
      let
        pkgs = import nixpkgs { system = "x86_64-linux"; };

        pythonPackages = pkgs.python3Packages;
      in pkgs.mkShell {
        buildInputs = [
          pkgs.vale
          pkgs.yarn

          pkgs.minikube
          pkgs.k9s
          pkgs.docker-compose

          # conda-store-server
          pythonPackages.yarl
          pythonPackages.requests
          pythonPackages.pydantic
          pythonPackages.pyyaml
          pythonPackages.traitlets
          pythonPackages.celery
          pythonPackages.uvicorn
          pythonPackages.fastapi
          pythonPackages.pyjwt
          pythonPackages.minio
          pythonPackages.filelock
          pythonPackages.sqlalchemy

          # conda-store
          pythonPackages.rich
          pythonPackages.click
          pythonPackages.aiohttp
          pythonPackages.ruamel-yaml

          # dev
          pythonPackages.pytest
          pythonPackages.black
          pythonPackages.flake8
          pythonPackages.build
          pythonPackages.setuptools
        ];

        shellHook = ''
          export CONDA_STORE_URL=http://localhost:5000/conda-store
          export CONDA_STORE_AUTH=basic
          export CONDA_STORE_USERNAME=username
          export CONDA_STORE_PASSWORD=password
        '';
      };
  };
}
