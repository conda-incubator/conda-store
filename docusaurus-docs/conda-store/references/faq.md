---
description: Frequently asked questions
---

# Frequently asked questions

## conda-store fails to build conda environment and worker is spontaneously killed (9 SIGKILL)

The following error most likely indicates that you have not allocated
enough memory to `conda-store-workers` for solving and building the
given environment. Solve this by increasing the memory allocated to
the container.

```shell
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

This issue occurs when the worker spontaineously dies. This can happen
for several reasons:

- worker is killed due to consuming too much memory (conda solver/builds can consume a lot of memory)
- worker was killed for other reasons e.g. forced restart
- bugs in conda-store

## What are the resource requirements for `conda-store-server`

<!-- TODO: Improve -->

`conda-store-server` is a web server and should not require any specific resources.
1 GB of RAM and 1 CPU should be plenty.

`conda-store-worker` does the actual builds of the conda environments.
Solving for conda environments can take a lot of memory in some circumstances.
Make sure to allocate at least 4 GB of RAM to the worker along with at least one CPU.
