# Crontabula 🧛

[![PyPI version](https://badge.fury.io/py/crontabula.svg)](https://badge.fury.io/py/crontabula)

Crontabula is a small library for parsing Crontab expressions into Python objects. The usage is simple:

```python
import crontabula

crontab = crontabula.parse("*/10 3,6 * * 1-4")
print(crontab.next)
# datetime.datetime(...)
```

## Installation

Install with:

```
pip install crontabula
```

## CLI

Crontabula comes with a small utility to print debug information about a crontab expression. Make sure you install the
library with the `cli` extra (`pip install "crontabula[cli]"`).

```
$ crontabula "*/15 * 1,15 * 1-5,6"
minute         0 15 30 45
hour           0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23
day of month   1 15
month          1 2 3 4 5 6 7 8 9 10 11 12
day of week    1 2 3 4 5 6
next time      2022-04-19 17:30:00 (in 0:03:59.987874)
```

## Contributing

Configure the environment and run the tests using [Poetry](https://python-poetry.org/):

```
$ poetry install
$ poetry run pre-commit install  # Optional, for linting with black
$ poetry run pytest
```
