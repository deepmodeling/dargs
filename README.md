# Argument checking for python programs

[![conda-forge](https://img.shields.io/conda/dn/conda-forge/dargs?color=red&label=conda-forge&logo=conda-forge)](https://anaconda.org/conda-forge/dargs)
[![pip install](https://img.shields.io/pypi/dm/dargs?label=pip%20install&logo=pypi)](https://pypi.org/project/dargs)
[![Documentation Status](https://readthedocs.org/projects/dargs/badge/)](https://dargs.readthedocs.io/)

This is a minimum version for checking the input argument dict.
It would examine argument's type,  as well as keys and types of its sub-arguments.

A special case called *variant* is also handled,
where you can determine the items of a dict based the value of on one of its `flag_name` key.

There are three main methods of `Argument` class:

- `check` method that takes a dict and see if its type follows the definition in the class
- `normalize` method that takes a dict and convert alias and add default value into it
- `gendoc` method that outputs the defined argument structure and corresponding docs

There are also `check_value` and `normalize_value` that
ignore the leading key comparing to the base version.

When targeting to html rendering, additional anchor can be made for cross reference.
Set `make_anchor=True` when calling `gendoc` function and use standard ref syntax in rst.
The id is the same as the argument path. Variant types would be in square brackets.

Please refer to test files for detailed usage.

## Additional features

- [PEP 484](https://peps.python.org/pep-0484/) type annotations
- Native integration with [Sphinx](https://github.com/sphinx-doc/sphinx), [DP-GUI](https://github.com/deepmodeling/dpgui), and [Jupyter Notebook](https://jupyter.org/)
- JSON encoder for `Argument` and `Variant` classes
- Generate [JSON schema](https://json-schema.org/) from an `Argument`, which can be further integrated with JSON editors such as [Visual Studio Code](https://code.visualstudio.com/)

## Loading from external files with `$ref`

Any dict that is processed by `check`, `check_value`, `normalize`, or `normalize_value`
may include a `"$ref"` key whose value is a path to an external file.
Before validation or normalization, dargs will load that file and merge its
contents into the dict, with any keys already present in the dict taking
precedence (local overrides).

Supported file formats:

- **JSON** (`.json`) — no extra dependencies required.
- **YAML** (`.yml` / `.yaml`) — requires [pyyaml](https://pypi.org/project/pyyaml/).
  Install it with `pip install pyyaml` or `pip install dargs[yaml]`.

Example — split a large config into reusable pieces:

```json
{
  "model": {
    "$ref": "model_defaults.json",
    "hidden_size": 256
  }
}
```

The contents of `model_defaults.json` are loaded first, then `"hidden_size": 256`
overrides (or adds to) the loaded values before the dict is validated or normalized.

