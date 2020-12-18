# brunette

🟤 A best practice Python code formatter

[![PyPI version](https://badge.fury.io/py/brunette.svg)](https://pypi.org/project/brunette/)

This is the "[black](https://github.com/psf/black)" formatter but with some improvements:

1. `--config` option supports `setup.cfg` format.
    * Where a `single-quotes` option enables single quotes as the preferred.
2. `--single-quotes` option to make single quotes the preferred.

## Installation

```bash
pip install brunette
```

## Usage

Use in the same way you would the 'black' formatter.

```bash
brunette *.py --config=setup.cfg
brunette *.py --line-length=79 --single-quotes
```

Example `setup.cfg`:

```
[tool:brunette]
line-length = 79
verbose = true
single-quotes = false
# etc, etc...
```

This can also be combined with Flake8's configuration:

```
[flake8]
# This section configures `flake8`, the python linting utility.
# See also https://flake8.pycqa.org/en/latest/user/configuration.html
ignore = E201,E202,E203
# E201 - whitespace after ‘(‘
# E202 - whitespace before ‘)’
# E203 - whitespace before ‘:’

# Exclude the git directory and virtualenv directory (as `.env`)
exclude = .git,.env

[tool:brunette]
line-length = 79
# etc, etc...
```

## Why does this need to exist?

- The current maintainer of Black, [refuses](https://github.com/psf/black/pull/633#issuecomment-445477386) to allow a single-quotes option. Due to his own *personal* preference (a preference which most of the Python community do not share).

- The current maintainer of Black, [refuses](https://github.com/psf/black/issues/683#issuecomment-542731068) to add setup.cfg support. Setup.cfg is the most widely used configuration file for Python projects. The maintainer of that library prefers "pyproject.toml" few people use at this time due to it's inflexibility and it requiring you to use Poetry, whatever that is.

- The current configuration file format as adopted by Black may conflict with the new _build isolation_ context with `pip`.  To avoid this, the use of a `setup.cfg` file is preferred but the policy is under review by the maintainers (https://github.com/pypa/pip/issues/8437#issuecomment-644196428).

## How to configure in VSCode

1. Get the full path to your brunette installation. In your terminal type:
  - `which brunette` (Linux)
  - `where brunette` (Windows)

In my case this looks like `/home/work/.pyenv/shims/brunette`. On Windows thats more like `C:\Python39\Scripts\brunette.exe`. Now copy whatever that value is.\

2. Open the [setttings](https://code.visualstudio.com/docs/getstarted/settings#_creating-user-and-workspace-settings) UI.

3. Search for *black*.
  - Paste that path into **Black Path**.
  - Set `black` as the Python Formatting Provider.
  - Add arguments as `--single-quotes` you like to the **Black Args**

![https://i.imgur.com/6EXoamM.png](https://i.imgur.com/6EXoamM.png)

3. That's it! Now whenever you [format your Python code](https://stackoverflow.com/a/48764668/13405802) brunette will be used.

## How to configure with Pre-Commit (https://pre-commit.com)

1. Run `pip install pre-commit` to install

2. Add a local repo option for brunette in `.pre-commit-config.yaml`

```
# See https://pre-commit.com for more information
# See https://pre-commit.com/hooks.html for more hooks
repos:
  - repo: https://github.com/odwyersoftware/brunette
    rev: b8fc75f460885f986a01842664e0571769b2cc12
    hooks:
      - id: brunette
  # Drop-in replacement for black with brunette
  # - repo: https://github.com/psf/black
  #   rev: stable
  #   hooks:
  #     - id: black
  #       language_version: python3.6
  - repo: https://gitlab.com/pycqa/flake8
    rev: 3.8.1
    hooks:
      - id: flake8
```

3. Run `pre-commit install` to install the Git pre-commit hook

3. Run `pre-commit run` to validate all files
