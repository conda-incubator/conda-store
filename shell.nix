let
  pkgs = import <nixpkgs> {};

  pythonPackages = pkgs.python3Packages;
in
pkgs.mkShell {
  buildInputs = [
    pkgs.docker-compose

    pythonPackages.pyyaml
    pythonPackages.flask
    pythonPackages.requests

    pythonPackages.black
    pythonPackages.flake8
  ];
}
