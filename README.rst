=======================
Flask Tactful Utilities
=======================

Utilities to allow tactful services to run using flask

Installation
============

1. Install python 3.8+
2. Install poetry `pip install poetry` or using these setps https://python-poetry.org/docs/#installation
3. Install dependencies `poetry install`

Upgrade to Python 3.9
=====================
- **Update Python Version**
    1. Open **`pyproject.toml`** file.
    2. Locate the **`[tool.poetry.dependencies]`** section.
    3. Update the **`python`** version to **`"~3.9"`**.
        
        ```toml
        [tool.poetry.dependencies]
        python = "~3.9"
        ```
        
    4. Save the changes.
- **Install Python 3.9**
    - On Ubuntu/Debian:
    
    ```bash
    sudo apt-get update
    sudo apt-get install python3.9
    sudo apt-get install python3.9-distutils
    ```
    
- **Update Poetry Environment**
    1. Open a terminal in the project directory.
    2. Run the following commands to update the Python version used by Poetry and recreate the virtual environment.
        
        ```bash
        poetry env use 3.9 
        [OR]
        poetry env use /usr/bin/python3.9
        
        poetry run pip install --upgrade pip setuptools
        
        poetry run poe login
        poetry install
        ```
        
- **Update Dependencies (Optional)**
    If there are newer versions of your dependencies that are compatible with Python 3.9, you may consider updating them. 
    
    ```bash
    poetry update
    ```
    
- **Verify the Python Version**        
    ```bash
    poetry run python --version
    ```
        

This should display Python 3.9.x.

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

NOTE: the pipelines publishes to AWS Artifiact Repo automatically on a tag push

.. code-block:: bash

    poetry run poe version

Alternatively you can publish manually using the following steps:

.. code-block:: bash

    poetry shell    # load virtual env to use poe task runner
    peo login       # run login task to load AWS code artifact credentials
    poetry version [minor|patch] # pump the version
    poe publish     # builds and publishes the new pumped version
    git commit -a -m "$(poetry version --short)" && git tag $(poetry version --short) && git push --tags && git push
