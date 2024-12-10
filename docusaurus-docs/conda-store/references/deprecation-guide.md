---
description: Deprecation guide
---

# Deprecation guide

This document outlines how conda-store deprecates functionality. Deprecation notices will always be available in release notes.

## Deprecations in the REST API

Deprecations in the REST API follow the form outlined by the [deprecation header RFC](https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-deprecation-header-02).

### Deprecating routes/endpoints

An endpoint that is deprecated will include the response headers:
```
{
   "Deprecation": "True", 
   "Sunset": <removal date, eg. "Mon, 16 Feb 2025 23:59:59 UTC" >
}
```

The "removal date" indicates the date after which conda store will no longer serve the endpoint. It will be specified as a [HTTP-Date](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Date)

## Deprecations in config

Config elements that are deprecated will be marked with a `deprecation` note in the docs and `--help` output. For example:
```
$ conda-store-server --help-all

...
--CondaStoreServer.enable_registry=<Bool>
   (deprecated) enable the docker registry for conda-store
   Default: False
...
```
