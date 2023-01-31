{
  description = "conda-store";

  inputs = {
    nixpkgs = { url = "github:yrd/nixpkgs/e622103f4b372b5cd8c0a189c2d819aa8f21c2d7"; };
  };

  outputs = inputs@{ self, nixpkgs, ... }: {
    devShell.x86_64-linux =
      let
        pkgs = import nixpkgs { system = "x86_64-linux"; };

        pythonPackages = pkgs.python3Packages;

        #pytest-base-url = pkgs.poetry2nix.mkPoetryApplication rec {
        #  projectDir = pkgs.fetchFromGitHub {
        #    owner = "pytest-dev";
        #    repo = "pytest-base-url";
        #    rev = "v2.0.0";
        #    sha256 = "0fbf5hv8ifyg4acdjclwv86gra1clsd10xmcld1vyycd6mx4pamz";
        #  };
        #  python = pythonPackages.python;
        #};

        ## built by poetry, so lots of library conflicts here
        #pytest-burl-path = "${pytest-base-url}/${pythonPackages.python.sitePackages}";

        #pytest-playwright = pythonPackages.buildPythonPackage rec {
        #  version = "0.3.0";
        #  pname = "pytest-playwright";
        #  disabled = pythonPackages.pythonOlder "3.7";

        #  src = pkgs.fetchFromGitHub {
        #    owner = "microsoft";
        #    repo = "playwright-pytest";
        #    rev = "v${version}";
        #    sha256 = "1m2g9gv2h2gj9qnnjsw453fjsqjaydc6mvpg2q14jj01nk2x0z3w";
        #  };

        #  postPatch = ''
        #    substituteInPlace setup.py \
        #        --replace 'playwright>=1.18' 'playwright' \
        #        --replace 'setup_requires=["setuptools_scm"],' ""
        #    # Replace the functionality of setuptools-scm
        #    echo 'version = "${version}"' > _repo_version.py
        #    export PYTHONPATH="''${PYTHONPATH}"
        #  '';

       #   dontUsePythonCatchConflicts = true;

       #   propagatedBuildInputs = [
       #     pythonPackages.playwright
       #     pythonPackages.pytest
       #     pythonPackages.python-slugify
       #   ];
       # };
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
          pythonPackages.psycopg2

          # conda-store
          pythonPackages.rich
          pythonPackages.click
          pythonPackages.aiohttp
          pythonPackages.ruamel-yaml

          # dev
       #   pytest-playwright
          pythonPackages.black
          pythonPackages.flake8
          pythonPackages.build
          pythonPackages.setuptools
          pythonPackages.alembic
        ];

        shellHook = ''
          export CONDA_STORE_URL=http://localhost:5000/conda-store
          export CONDA_STORE_AUTH=basic
          export CONDA_STORE_USERNAME=username
          export CONDA_STORE_PASSWORD=password

          export PYTHONPATH="''${PYTHONPATH}"
          export PLAYWRIGHT_BROWSERS_PATH=${pkgs.playwright.browsers}
        '';
      };
  };
}
