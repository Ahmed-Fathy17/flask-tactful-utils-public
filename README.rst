=======================
Flask Tactful Utilities
=======================

Utilities to allow tactful services to run using flask

Installation
============

1. Install python 3.8+
2. Install poetry `pip install poetry` or using these setps https://python-poetry.org/docs/#installation
3. Install dependencies `poetry install`

Developer Guide
===============

A full documentation of the library and its functions can be downloaded from a single HTML file here: 
https://bitbucket.org/slickblox/flask-tactful-utils/downloads/index.html

Testing 
==========

.. code-block:: bash

    poetry run pytest


Publishing
==========

.. code-block:: bash

    poetry shell    # load virtual env to use poe task runner
    peo login       # run login task to load AWS code artifact credentials
    poetry version [minor|patch] # pump the version
    poetry build    # build the library
    poetry publish -r aws   # publish to AWS artifact repo
    git commit -a . && git tag $(poetry version --short) && git push --tags
