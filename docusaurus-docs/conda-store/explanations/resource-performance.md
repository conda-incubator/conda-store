---
description: Requirements to run conda-store
---

# Machine requirements

## Resource Requirements

`conda-store-server`` is a web server and should not require any specific resources.
1 GB of RAM and 1 CPU should be plenty.

`conda-store-worker`` does the actual builds of the conda environments.
Solving for conda environments can take a lot of memory in some circumstances.
Make sure to allocate at least 4 GB of RAM to the worker along with at least one CPU.

## Performance

There are several parts of conda-store to consider for performance. We have tried to list them in order of performance impact that may be seen.

### Worker Storage

When conda-store builds a given environment it has to locally install the environment in the directory specified in the Traitlets configuration CondaStore.store_directroy. Conda environments consist of many hardlinks to small files. This means that the store_directory is limited to the number of IOPS the directory can perform. Many cloud providers have high performance storage options. These include:

If you do not need to mount the environments via NFS into the containers we highly recommend not using NFS and using traditional block storage. Not only is it significantly cheaper but the IOPs performance will be better as well.

If you want to mount the environments in containers or running VMs NFS may be a good option for you. With NFS many cloud providers provide a high performance filesystem option at a significant premium in cost. Example of these include GCP Filestore, AWS EFS, and Azure files. Choosing an nfs storage option with low IOPS will result in long environment install times.

### Network Speed

While Conda does its best to cache packages, it will have to reach out to download the repodata.json along with the packages as well. Thus network speeds may be important. Typically cloud environments have plenty fast Internet.

### S3 Storage

All build artifacts from conda-store are stored in object storage that behaves S3 like. S3 traditionally has great performance if you use the cloud provider implementation.
