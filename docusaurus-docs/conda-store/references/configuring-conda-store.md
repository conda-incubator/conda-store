---
description: configuring conda-store
---

# Configuring conda-store

The conda-store server has two types of config. 

* server configuration config, eg. url for database endpoints, redis
endpoints, port to run on, etc.
* application settings config, eg. the default namespace, default conda
command, default packages to install in environments, etc.

The server configuration is always specified in the [conda-store configuration file](./configuration-options.md).

There are two options to set the application settings config. These
are through:

* the conda-store configuration file. See the available options in the 
  [configuration options doc](./configuration-options.md)
* the conda-store admin console. Available at `<conda_store_url>/admin`

There are multiple levels which config can be applied to conda store. 

* deployment defaults (controlled by the config file)
* global defaults (controlled by the admin console)
* namespace defaults (controlled by the admin console)
* environment default (controlled by the admin console)

The most specific config will take precedence over the more  general 
setting. For example, if the `conda_command` is specified in all four
config levels, the most specific, environment config will be applied.

The full list of application config settings is described in the 
[settings pydantic model](https://github.com/conda-incubator/conda-store/blob/main/conda-store-server/conda_store_server/_internal/schema.py#L203).
