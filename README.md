# brunette

This is the [black](https://github.com/psf/black) formatter but with some improvements:

1. `--config` option supports `setup.cfg` format.
2. Adds `single-quotes` to enable single quotes as the preferred.

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
```

## Why does this need to exist?

- The current maintainer of black, [refuses](https://github.com/psf/black/pull/633#issuecomment-445477386) to allow a single-quotes option. Due to his own *personal* preference (a preference which most of the Python community do not share).

- The current maintainer of black, [refuses](https://github.com/psf/black/issues/683#issuecomment-542731068) to add setup.cfg support. Setup.cfg is the most widely used configuration file for Python projects. The maintainer of that library prefers "project.tolm" few people use at this time due to it's inflexibility and it requiring you to use Peotry, whatever that is.

