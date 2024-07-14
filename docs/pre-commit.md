# Pre-commit hooks

To check JSON files (available as of dargs v0.4.8) via [pre-commit](https://github.com/pre-commit/pre-commit), add the following to your `.pre-commit-config.yaml`:

```yaml
-   repo: https://github.com/deepmodeling/dargs
    rev: v0.4.8
    hooks:
    -   id: dargs-check
        # Specify the function to return arguments
        args: ["-f dargs._test.test_arguments"]
        # Pattern of JSON files to check
        files: "tests/test_arguments.json"
        # Add additional Python dependencies for arguments
        additional_dependencies: []
```
