from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / 'README.md').read_text(encoding='utf-8')


setup(
    name='conda-store-server',
    version='0.2.5',
    description='Conda Environment Management, Builds, and Serve',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/Quansight/conda-store',
    author='Christopher Ostrouchov',
    author_email='chris.ostrouchov@gmail.com',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3 :: Only',
    ],
    keywords='conda',
    packages=find_packages(where='.'),
    install_requires=[
        'conda-docker',
        'conda-pack',
        'sqlalchemy',
        'psycopg2',
        'requests',
        'flask',
        'flask-cors',
        'pyyaml',
        'pydantic',
        'minio',
    ],
    extras_require={
        'dev': [
            'pytest',
            'pytest-mock',
            'black==19.10b0',
            'flake8',
            'sphinx',
            'recommonmark',
            'sphinx_rtd_theme'
        ],
    },
    entry_points={
        'console_scripts': [
            'conda-store-server=conda_store_server.__main__:main',
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/quansight/conda-store",
        "Documentation": "https://conda-store.readthedocs.io/",
        "Source": "https://github.com/quansight/conda-store",
    },
)
