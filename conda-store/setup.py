import os
from jupyter_packaging import (
        create_cmdclass, install_npm, ensure_targets,
        combine_commands, skip_if_exists
        )
import setuptools

HERE = os.path.abspath(os.path.dirname(__file__))
LAB_PATH = os.path.join(HERE, "conda_store", "labextension")

cmdclass = create_cmdclass(
    "jsdeps",
    package_data_spec={
        "conda_store": [
            "*"
        ]
    },
    data_files_spec=[
        ("share/jupyter/labextensions/%s" % "@Quansight/conda-store", LAB_PATH, "**"),
        ("share/jupyter/labextensions/%s" % "@Quansight/conda-store", HERE, "install.json"),
    ]
)

js_command = combine_commands(
    install_npm(HERE, build_cmd="build:prod", npm=["jlpm"]),
    ensure_targets([
        os.path.join(LAB_PATH, "package.json"),
    ]),
)

if os.path.exists(os.path.join(HERE, ".git")):
    cmdclass["jsdeps"] = js_command
else:
    cmdclass["jsdeps"] = skip_if_exists([
        os.path.join(LAB_PATH, "package.json"),
    ], js_command)

with open("README.md", "r") as fh:
    long_description = fh.read()

setup_args = dict(
    name="conda_store",
    version='0.2.0',
    url="https://github.com/Quansight/conda-store",
    author="Anirrudh Krishnan",
    description="A JupterLab Extension and client to interface with conda-store",
    long_description=long_description,
    long_description_content_type="text/markdown",
    cmdclass=cmdclass,
    packages=setuptools.find_packages(),
    install_requires=[
        "jupyterlab>=3.0.0",
    ],
    zip_safe=False,
    include_package_data=True,
    python_requires=">=3.6",
    license="BSD-3-Clause",
    platforms="Linux, Mac OS X, Windows",
    keywords=["Jupyter", "JupyterLab", "JupyterLab3", "conda-store"],
)


if __name__ == "__main__":
    setuptools.setup(**setup_args)
