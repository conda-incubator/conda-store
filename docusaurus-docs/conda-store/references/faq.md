---
description: Frequently asked questions
---

# Frequently asked questions

## conda-store fails to build Conda environment and worker is spontaneously killed (9 SIGKILL)

The following error most likely indicates that you have not allocated
enough memory to `conda-store-workers` for solving and building the
given environment. Solve this by increasing the memory allocated to
the container.

```bash
Process 'ForkPoolWorker-31' pid:90 exited with 'signal 9 (SIGKILL)'

Task handler raised error: WorkerLostError('Worker exited prematurely: signal 9 (SIGKILL) Job: 348.')

Traceback (most recent call last):
File "/opt/conda/envs/conda-store-server/lib/python3.9/site-packages/billiard/pool.py", line 1265, in mark_as_worker_lost

    raise WorkerLostError(

billiard.exceptions.WorkerLostError: Worker exited prematurely: signal 9 (SIGKILL) Job: 348.
```

## Why are environment builds stuck in building state?

Recently conda-store added a feature to cleanup builds which are stuck
in the BUILDING state and are not currently running on the
workers. This feature only works for certain brokers
e.g. redis. Database celery brokers are not supported.

This issue occurs when the worker spontaneously dies. This can happen
for several reasons:

- worker is killed due to consuming too much memory (conda solver/builds can consume a lot of memory)
- worker was killed for other reasons e.g. forced restart
- bugs in conda-store

## Build path length

Conda packages are guaranteed to be [relocatable] as long as the environment
prefix length is `<=` 255 characters. In conda-store, the said prefix is specified
in `Build.build_path`. When building an environment, you might see an error like
this:

```bash
build_path too long: must be <= 255 characters
```

If so, try configuring the conda-store `CondaStore.store_directory` to be as
close to the filesystem root as possible. Additionally, 255 characters is also a
common limit for individual files on many filesystems. When creating
environments, try using shorter `namespace` and `environment` names since they
affect both the `build_path` length and the filename length.

[relocatable]: https://docs.conda.io/projects/conda-build/en/latest/resources/make-relocatable.html

## Build key versions

The part of the build path that identifies a particular environment build is the
build key. Originally, conda-store used the following format, known as version
1:

```bash
c7afdeffbe2bda7d16ca69beecc8bebeb29280a95d4f3ed92849e4047710923b-20231105-035410-510258-12345678-this-is-a-long-environment-name
^ (1)                                                            ^ (2)                  ^ (3)    ^ (4)
```

It consists of:
1. a SHA-256 hash of the environment specification
   (`CondaSpecification`, which represents a user-provided environment, is
   converted to a dict and passed to `datastructure_hash`, which recursively sorts
   it and calculates the SHA-256 hash)
2. a human-readable timestamp (year, month, day, `-`, hour, minute, second, `-`, microsecond)
3. the id of a build
4. the environment name.

To help mitigate build path length issues, a shorter build key format was
introduced, known as version 2:

```bash
c7afdeff-1699156450-12345678-this-is-a-long-environment-name
^ (1)    ^ (2)      ^ (3)    ^ (4)
```

It consists of:
1. a truncated SHA-256 hash of the environment specification
   (`CondaSpecification`, which represents a user-provided environment, is
   converted to a dict and passed to `datastructure_hash`, which recursively sorts
   it and calculates the SHA-256 hash)
2. a Unix timestamp
3. the id of a build
4. the environment name.

However, version 2 build paths don't solve the problem completely because they
include user-provided data, like the environment name, and that data can be
arbitrary large.

To solve this problem, version 3 was introduced, which will always have the same
size. It looks like this:

```bash
64a943764b70e8fe181643404894f7ae
```

It's a truncated SHA-256 hex digest, which is calculated based on:

- namespace name
- specification hash (also SHA-256)
- build timestamp
- build id.

See `BuildKey._version3_fmt` for details.

:::note
When version 3 is used, `Build.build_path` will not include the namespace name,
because it's not fixed size, so all builds will be placed right into
`CondaStore.store_directory`.

Additionally, `CondaStore.environment_directory` will be completely ignored, so
no symlinks connecting an environment name to its corresponding build will be
created, because the environment directory format also includes variable-size
data (the namespace and environment names).

The lack of symlinks doesn't prevent server artifacts from being generated,
which are available for download via the UI (lockfiles, archives, etc.), because
those rely on storage or use the database.

But it does impact conda integration or tools that rely on it, like when
conda-store is used with JupyterLab as part of a Nebari deployment. Without
environment symlinks, there'll be no way to tell conda where to look for
environments, which is done by setting `envs_dirs` in `.condarc`, so `conda env
list` will return nothing and no environments will show up in JupyterLab.
:::

The version 2 format is the default because it supports environment symlinks and
doesn't usually run into path length limitations. If you do experience problems
with the latter and don't need the former, then consider using the version 3
format.

No matter what format you choose, environments that were previously created
using other version formats will be accessible in the conda-store web UI.

There is no real reason to use version 1 format anymore, but any version can be
explicitly set via the config, for example:

```python
c.CondaStore.build_key_version = 1
```

## Long paths on Windows

conda-store supports Windows in standalone mode. However, when creating
environments with certain packages, you may see errors like:

```bash
ERROR:root:[WinError 206] The filename or extension is too long: 'C:\\...'
```

This error is due to the fact that Windows has a limitation that file paths
cannot be more than 260 characters.

See [conda-store issue #588][max-path-issue] for more details.

### Solution 1: Extended-length path prefix (`\\?\`)

If you *don't have administrator privileges*, try using the following config
option:

```python
c.CondaStore.win_extended_length_prefix = True
```

This adds the extended-length path prefix (`\\?\`) to conda-store `build_path`
and `environment_path` methods, which should allow for a maximum total path
length of 32,767 characters when building packages.

See [this Microsoft support article][max-path] for more details on the
extended-length path prefix.

### Solution 2: `LongPathsEnabled`

If you *have administrator privileges*, set the registry key
`Computer\HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem\LongPathsEnabled
(Type: REG_DWORD)` to `1`, which removes this `MAX_PATH` limitation.

See [this Microsoft support article][max-path] for more details on how to set
this registry key.

### Solution 3: `store_directory`

If it is not possible to set the registry key, for instance, because you *do
not have access to administrator privileges*, you should configure the
conda-store `CondaStore.store_directory` to be as close to the filesystem root
as possible, so that the total length of the paths of package files is
minimized.

### Solution 4: `build_key_version`

Use the short build key version as explained [above](#build-key-versions):

```python
c.CondaStore.build_key_version = 2
```

[max-path-issue]: https://github.com/conda-incubator/conda-store/issues/588
[max-path]: https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation

## What are the resource requirements for `conda-store-server`

`conda-store-server` is a web server and should not require any specific resources.
1 GB of RAM and 1 CPU should be plenty.

`conda-store-worker` does the actual builds of the conda environments.
Solving for conda environments can take a lot of memory in some circumstances.
Make sure to allocate at least 4 GB of RAM to the worker along with at least one CPU.
