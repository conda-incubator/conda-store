{ pkgs ? import <nixpkgs> { }, pythonPackages ? pkgs.python3Packages }:

pkgs.mkShell {
  buildInputs = [
    pkgs.vagrant
    pkgs.ansible
  ];
}
