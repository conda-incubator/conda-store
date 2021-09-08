Conda-Store
===========

End users think in terms of environments not packages. The core
philosophy of conda-store is to serve identical conda environments in
as many ways as possible to users and services. Conda-store was
developed due to a significant need in enterprise architectures.

.. image:: _static/images/conda-store-authenticated.png
  :alt: Conda Store Homepage

Use Cases
---------

IT and Development Team Friction
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We saw tension between the IT/sysadmins and developers who use the
environments that they build. When IT gets a request for a new package
in an environment, they need to rebuild the environments and check that
the package satisfies their constraints. This process may take several
days and at best will not be immediate. While developers need packages
in their environments as soon as possible to do interesting new
research. This situation often led to a lot of frustration on both
sides for good reason. Conda-store aims to address this by allowing
users to control a set of environments in their namespace while
allowing IT to having all environments under their control.

Reproducibly Productionizing Environments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Another issue we saw was the need to quickly productionize workflows
and ensure that they may run for many years to come. Often times
developers will experiment with a given environment and create a
notebook to run a given workflow. They will want to "submit" this
notebook with the given environment and run it on a cron job. The only
problem is that this creates a huge burden on IT. How is IT supposed
to ensure that the environment that that notebook ran with is
preserved indefinitely? Conda-store addresses this by building all
environment separately(including updates). There is a unique key that
identifies any given environment. Furthermore this environment is
available in many different forms: yaml, lockfile, conda tarball, and
docker image. The advantage here is that the workflow orchestration
framework may run significantly different from the developer
environment and we need a way to ensure that environments are the
same.

Removing the Need for Curated Docker Environments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

While this point may be slightly docker focused the point is that
containers are used everywhere. The burden of creating images with
given packages can be cumbersome. There are tools that make this
easier e.g. `repo2docker <https://github.com/jupyterhub/repo2docker>`_
however these project seem focused on bundling the data/repo with the
image. Conda-store has a feature to build on demand environments based
on the image name. For example the image name
`localhost:5000/conda-store-dynamic/numpy/jupyterlab/scipy.gt.1.0`
will create a docker image with `numpy`, `jupyterlab`, and `scipy >
1.0`. This feature was inspired by `nixery
<https://nixery.dev/>`_. The `example/kubernetes` directory has a
working test that demonstrates this.

Features
--------

Conda Store controls the environment lifecycle: management, builds,
and serving of environments.

It **manages** conda environments by:

 - provides a web ui to take advantage of many of conda-stores
   advanced capabilities and providing an easy interface to modify
   environments
 - watching specific files or directories for changes in environment
   filename specifications
 - provides a REST api for managing environments (which a jupyterlab
   plugin is being actively developed for)
 - provides a command line utility for interacting with conda-store
   conda-store env [create, list]
 - full role based access controls (rbac) around environment view,
   creation, update, and deletion.

It **builds** conda specifications in a scalable manner using N
workers communicating using Celery to keep track of queued up
environment builds.

It **serves** conda environments via a filesystem, lockfiles,
tarballs, and soon a docker registry. Tarballs and docker images can
carry a lot of bandwidth which is why conda-store integrates
optionally with s3 to actually serve the blobs.

Contents
========

.. toctree::
   :maxdepth: 2

   installation
   user_guide
   administration
   contributing

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
