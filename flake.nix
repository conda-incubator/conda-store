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
          pkgs.docker-compose

          pythonPackages.yarl
          pythonPackages.requests
          pythonPackages.pydantic
          pythonPackages.pyyaml
          pythonPackages.traitlets
          pythonPackages.celery
          pythonPackages.flask
          pythonPackages.flask-cors
          pythonPackages.pyjwt
          pythonPackages.minio
        ];
      };
  };
}
