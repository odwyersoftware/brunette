# brunette

🟤 A best practice Python code formatter

[![PyPI version](https://badge.fury.io/py/brunette.svg)](https://pypi.org/project/brunette/)

This is the "[black](https://github.com/psf/black)" formatter but with some improvements:

1. `--config` option supports `setup.cfg` format.
2. Adds `single-quotes` option to enable single quotes as the preferred.

## Installation

```bash
pip install brunette
```

## Usage

Use in the same way you would the 'black' formatter.

```bash
brunette *.py --config=setup.cfg
```

Example `setup.cfg`:

```
[tool:brunette]
line-length = 79
verbose = true
single-quotes = false
# etc, etc.
```

## Why does this need to exist?

- The current maintainer of black, [refuses](https://github.com/psf/black/pull/633#issuecomment-445477386) to allow a single-quotes option. Due to his own *personal* preference (a preference which most of the Python community do not share).

- The current maintainer of black, [refuses](https://github.com/psf/black/issues/683#issuecomment-542731068) to add setup.cfg support. Setup.cfg is the most widely used configuration file for Python projects. The maintainer of that library prefers "project.tolm" few people use at this time due to it's inflexibility and it requiring you to use Poetry, whatever that is.



## How to configure in VSCode

1. In your terminal type `which brunette` to get the full path to your brunette installation.

In my case this looks like `/home/work/.pyenv/shims/brunette`. Now copy whatever that value is.

1. Open the [setttings](https://code.visualstudio.com/docs/getstarted/settings#_creating-user-and-workspace-settings) UI.

2. Search for *black*.

- Paste that path into "Black Path".
- Set black as the Python Formatting Provider.

![https://i.imgur.com/6EXoamM.png](https://i.imgur.com/6EXoamM.png)

3. That's it! Now whenever you [format your Python code](https://stackoverflow.com/a/48764668/13405802) brunette will be used.
