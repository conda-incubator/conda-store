let
  pkgs = import <nixpkgs> {};

  pythonPackages = pkgs.python3Packages;
in
pkgs.mkShell {
  buildInputs = [
    pythonPackages.pyyaml
    pythonPackages.flask
    pythonPackages.psutil

    pythonPackages.black
    pythonPackages.flake8
  ];
}
