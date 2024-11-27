#!/bin/bash

# Requirements
# - packages
#   - github-activity https://github.com/choldgraf/github-activity
#   - jq
# - GITHUB_ACCESS_TOKEN env var set
# - `conda-store-server-dev` conda env is activated

function usage {
    echo -e "Usage: ./cut-release-pr.sh -r release_version -c conda_store_ui_version\n"
    exit 1
}

function build_and_check () {
    # Runs a hatch build, twine check, and checks the version of the package
    # Assumes that you are in the directory for the package
    #
    # args:
    #   CHECK_TARGET: the name of the package to check
    CHECK_TARGET=$1

    echo "${CHECK_TARGET}: Checking hatch versions..."
    HV=$(hatch version)
    if [[ "$HV" == "$RELEASE_VERSION" ]]; then
        echo "${CHECK_TARGET}: hatch version matches ${RELEASE_VERSION}"
    else
        echo "${CHECK_TARGET}: hatch version does not match the requested release version. Something has gone wrong, exiting!"
        exit 1
    fi

    echo "${CHECK_TARGET}: Running build and checking package..."
    hatch build
    rc=$(twine check dist/*)
    if [[ $rc =~ "FAILED" ]]; then
        echo "${CHECK_TARGET}: package is not in a good state, exiting!"
        exit 1
    else
        echo "${CHECK_TARGET}: package is in a good state"
    fi

    echo "${CHECK_TARGET}: cleaning up..."
    hatch clean
}

while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -h|--help)
    usage
    exit 0
    shift
    shift
    ;;
    -r|--release_version)
    RELEASE_VERSION="$2"
    shift
    shift
    ;;
    -c|--conda_store_ui_version)
    CONDA_STORE_UI_VERSION="$2"
    shift
    shift
    ;;
    *)
    usage
    exit 0
    shift
    ;;
esac
done

CURRENT_DATE=$(date '+%Y-%m-%d')

echo "Today is ${CURRENT_DATE}
Building a release for
  * conda-store version ${RELEASE_VERSION}
with
  * conda-store-ui version ${CONDA_STORE_UI_VERSION}
"

# prepare repo
git checkout -b release-"$RELEASE_VERSION"
git clean -fxdq

# bump versions
sed -E -r -i "s/__version__ = .+/__version__ = \"$RELEASE_VERSION\"/g" conda-store-server/conda_store_server/__init__.py
sed -E -r -i "s/__version__ = .+/__version__ = \"$RELEASE_VERSION\"/g" conda-store/conda_store/__init__.py
sed -E -r -i "s/CONDA_STORE_UI_VERSION = .+/CONDA_STORE_UI_VERSION = \"$CONDA_STORE_UI_VERSION\"/g" conda-store-server/hatch_build.py

# create changelog
LATEST_TAG=$(curl https://api.github.com/repos/conda-incubator/conda-store/releases | jq -r '.[0].tag_name')
PYTHONWARNINGS="ignore" github-activity conda-incubator/conda-store --since $LATEST_TAG --heading-level=2 > tmp_changes.txt
# remove first line of changes - it's always a message about which GH token is used
sed -n -i '1!p' tmp_changes.txt
# replace the header for the changes with the appropriate title
sed -n -i '1!p' tmp_changes.txt
sed -i "1s/^/## [$RELEASE_VERSION] - $CURRENT_DATE\n/" tmp_changes.txt
# insert changes into changelog
sed -i "/---/r tmp_changes.txt" CHANGELOG.md
# clean up temp file
rm tmp_changes.txt

cd conda-store-server
build_and_check conda-store-server
cd ..

cd conda-store
build_and_check conda-store
cd ..


# add files to git
git add conda-store conda-store-server CHANGELOG.md
git commit -m "REL - $RELEASE_VERSION"

echo "
Finished preparing the release!

Next steps:
  * Validate that the changes made are correct
  * Follow any testing/validation steps
  * Push them changes up to github

    git push origin release-"$RELEASE_VERSION"
"
