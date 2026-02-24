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
