# Flask Tactful Utilities

Utilities to allow tactful services to run using flask

## Installation

1. Install python 3.8+
2. Install poetry `pip install poetry` or using these setps https://python-poetry.org/docs/#installation
3. Install dependencies `poetry install`

## Testing 

```
poetry run pytest
```

## Publishing

```
poetry shell    # load virtual env to use poe task runner
peo login       # run login task to load AWS code artifact credentials
poetry build    # build the library
poetry publish -r aws   # publish to AWS artifact repo

```