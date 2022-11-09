:html_theme.sidebar_secondary.remove:

.. rst-class:: hide

conda-store
===========

.. toctree::
   :maxdepth: 2
   :hidden:

   installation
   user_guide
   administration
   contributing
   api

.. image:: _static/images/conda-store-logo-vertical-lockup.png
    :alt: conda-store logo mark
    :scale: 50%
    :align: center
    :class: dark-light p-2


.. rst-class:: center

**Data science environments, for collaboration.**

----

conda-store is a tool for managing data science environments, in collaborative settings.
It provides flexible yet reproducible environments, while enforcing best practices for your team.

The conda packaging system works for individual users, but it can be tricky to reliably reproduce environments to share them with colleagues.
On the other hand, Docker containers can ensure reproducibility, but aren't friendly to individual users who may need new packages or versions for daily work.
We created conda-store to resolve this.

.. panels::
    :container: container-lg pb-3
    :column: col-lg-4 col-md-4 col-sm-6 col-xs-12 p-2

    **Flexible**
    ^^^^^^^^^^^^^^

    Create and update environments with the Graphical UI or a YAML editor.

    Environments are automatically version-controlled and all versions are readily available.

    ---
    **Reproducible**
    ^^^^^^^^^^^^^^^^^^

    Share environments quickly through the auto-generated artifacts including a lockfile, docker image, YAML file, and tarball.

    Exact versions of all packages and their dependencies are pinned in all the auto-generated artifacts.

    ---
    **Goveranance**
    ^^^^^^^^^^^^^

    Access admin-approved packages and channels, and request new ones when needed.

    Admins can insert or require certain packages and versions for organization-level compatibility.

    Admins can manage users' access-levels using "Namespaces", and allow users to share environments across (and only with) their team.
