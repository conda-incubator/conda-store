---
sidebar_position: 1
description: Guidelines for contributing to various conda-store projects
---

# Contribution guidelines

## Issues and pull requests

## Git setup

## Local development setup

## Testing

## Guidelines for specific workflows

### Changes to API

The REST API is considered somewhat stable. If any changes are made to
the API make sure the update the OpenAPI/Swagger specification in
`docs/_static/openapi.json`. This may be downloaded from the `/docs`
endpoint when running conda-store. Ensure that the
`c.CondaStoreServer.url_prefix` is set to `/` when generating the
endpoints.
