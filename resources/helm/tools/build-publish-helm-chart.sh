#!/bin/bash
# This script publishes the Helm chart to the Quansight Helm chart repo and pushes
# associated built docker images to DockerHub using chartpress.
# --------------------------------------------------------------------------

# Exit on errors, assert env vars, log commands
set -eux

PUBLISH_ARGS="--push --publish-chart \
    --builder=docker-buildx \
    --platform=linux/amd64 \
    --platform=linux/arm64
"

# chartpress needs to run next to resources/helm/chartpress.yaml
cd resources/helm/

# chartpress use git to push to our Helm chart repository.
# Ensure that the permissions to the Docker registry are
# already configured.

if [[ $GITHUB_REF != refs/tags/* ]]; then
    # Using --extra-message, we help readers of merged PRs to know what version
    # they need to bump to in order to make use of the PR.
    #
    # ref: https://github.com/jupyterhub/chartpress#usage
    #
    # NOTE: GitHub merge commits contain a PR reference like #123. `sed` is used
    #       to extract a PR reference like #123 or a commit hash reference like
    #       @123abcd.

    PR_OR_HASH=$(git log -1 --pretty=%h-%B | head -n1 | sed 's/^.*\(#[0-9]*\).*/\1/' | sed 's/^\([0-9a-f]*\)-.*/@\1/')
    LATEST_COMMIT_TITLE=$(git log -1 --pretty=%B | head -n1)
    EXTRA_MESSAGE="${GITHUB_REPOSITORY}${PR_OR_HASH} ${LATEST_COMMIT_TITLE}"

    chartpress $PUBLISH_ARGS --extra-message "${EXTRA_MESSAGE}"
else
    # Setting a tag explicitly enforces a rebuild if this tag had already been
    # built and we wanted to override it.

    chartpress $PUBLISH_ARGS --tag "${GITHUB_REF:10}"
fi
