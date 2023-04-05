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
    :alt: conda-store logo
    :scale: 50%
    :align: center
    :class: dark-light p-2


.. rst-class:: center

**Data science environments, for collaboration.**

----

.. rst-class:: center

conda-store is an open source tool for managing data science environments in collaborative teams.
It provides flexible, yet reproducible, environments while enforcing best practices throughout your environment's life cycle.

.. panels::
    :container: container-lg pb-3
    :column: col-lg-4 col-md-4 col-sm-6 col-xs-12 p-2

    **🧶  Flexible**
    ^^^^^^^^^^^^^^

    .. rst-class:: left

    Create and update environments quickly using a graphical UI or a YAML editor.

    .. rst-class:: left

    All environments are automatically version-controlled, and available for use.

    ---
    **💫  Reproducible**
    ^^^^^^^^^^^^^^^^^^

    .. rst-class:: left

    Share environments effortlessly through the auto-generated artifacts: lockfile, docker image, YAML file, or tarball.

    .. rst-class:: left

    Exact versions of all packages and their dependencies are pinned in these artifacts.

    ---
    **⚖️  Governance**
    ^^^^^^^^^^^^^

    .. rst-class:: left

    Access admin-approved packages and channels, and request new ones when needed.

    .. rst-class:: left

    Admins have role-based access management, to allow users to share environments across (and only with) their team.

.. rst-class:: center

The conda packaging system works well for individual users, but it can get tricky to reproduce environments reliably to share with colleagues. On the other hand, Docker containers can ensure reproducibility, but aren't friendly to individual users who may need new packages or versions for daily work. conda-store resolves this friction, and provides a balance of both the familiarity of conda and the robustness of containers.


.. rst-class:: border

.. figure:: _static/images/conda-store-ui.webp
    :alt: conda-store video
    :align: center
    :class: dark-light p-2

    Preview of a new graphical user interface for conda-store, which will also be available as a JupyterLab extension!
