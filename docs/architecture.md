# Conda Store

Conda Store itself is a collection of services:
 - conda build worker :: N conda build workers to build queued conda environments
 - conda rest api :: rest api for creating new environments
 - conda web ui :: flask webserver view of conda store
 - conda docker registry :: a python implementation of a docker registry with tight integration with conda-store
