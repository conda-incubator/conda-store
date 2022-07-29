import sys
import re
import pathlib
import shlex

from conda_store.cli import cli


def detect_shebang():
    """Enable conda-store run within shebangs

    Running `conda-store run ...` within shebangs enables environments
    within shell scripts on OSX and Linux (sadly windows not supported
    here since there is no concept of shebangs).

    Feature inspired by nix-shell shebangs see:
      - usage :: https://nixos.wiki/wiki/Nix-shell_shebang
      - implementation :: https://github.com/nixos/nix/blob/7a9ac91a43e1e05e9df9d1b9b4a2cf322d62bb1c/src/nix-build/nix-build.cc#L108-L130
    """

    filename = pathlib.Path(sys.argv[1]).resolve()
    args = ["conda-store", "run"]

    try:
        with filename.open() as f:
            line = f.readline()
            # shebangs are common within entrypoints in python scripts
            # so we must be strict and the specification for shebangs
            # is quite limiting
            if re.fullmatch(r"^#!.*conda-store\s*$", line.strip()):
                for line in f:
                    match = re.fullmatch(r"^#!\s*conda-store run (.*)$", line.strip())
                    if match:
                        for token in shlex.split(match.group(1)):
                            args.append(token)
                args.append(str(filename))
                sys.argv = args
    except Exception:
        pass


def main():
    detect_shebang()
    cli()


if __name__ == "__main__":
    main()
