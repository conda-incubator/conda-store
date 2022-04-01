{
  description = "Conda-Store";

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

          pkgs.minikube
          pkgs.k9s
          pkgs.docker-compose

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

          pythonPackages.pytest
        ];
      };
  };
}
