---
description: Learn to make conda-store performant
---

# Performance

Several components can impact conda-store's overall performance.
They are listed and described in order of decreasing impact below.

## Worker storage

When conda-store builds a given environment it has to locally install the environment in the directory specified in the [Traitlets][traitlets] configuration `CondaStore.store_directory`.
Conda environments consist of many hardlinks to small files.
This means that the performance of `store_directory` is limited to the number of
[Input/output operations per second (IOPS)][IOPS-wikipedia] the directory can
perform.
Many cloud providers have high performance storage options you can consider.

### When to use NFS

If you do not need to mount the environments via NFS into the containers, it's recommend to not use NFS and instead use traditional block storage.
Not only is it significantly cheaper, but also the IOPS performance will be better.

If you want to mount the environments in containers or running VMs, then NFS
may be a good option.
With NFS, many cloud providers provide a high performance filesystem option at a significant premium in cost, like [GCP Filestore][gcp-filestore], [Amazon EFS][aws-efs], and [Azure Files][azure-files].

:::note
Choosing an NFS storage option with low IOPS will result in long environment
creation times.
:::

## Network speed

While conda does its best to cache packages, it will have to connect over the internet
to download the `repodata.json` along with the packages.
Thus network speeds can impact performance, but typically cloud environments have plenty fast Internet.

## Artifact storage

All build artifacts from conda-store are stored in object storage that behaves like [Amazon S3][amazon-s3].
S3 traditionally has great performance if you use the cloud provider implementation.

<!-- External links -->

[amazon-s3]: https://aws.amazon.com/s3/
[traitlets]: https://traitlets.readthedocs.io/en/stable/using_traitlets.html
[iops-wikipedia]: https://en.wikipedia.org/wiki/IOPS
[gcp-filestore]: https://cloud.google.com/filestore/docs/performance#expected_performance
[aws-efs]: https://aws.amazon.com/efs/features/
[azure-files]: https://docs.microsoft.com/en-us/azure/storage/files/understanding-billing#provisioning-method
