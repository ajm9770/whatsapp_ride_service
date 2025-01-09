# Development Configuration Files

This directory contains configuration files for various development tools used in the project.

## Files

### `.flake8`
Configuration for the Flake8 linter, including:
- Maximum line length
- Ignored rules
- Import order style
- Docstring conventions

### `mypy.ini`
Configuration for MyPy type checker:
- Python version
- Strictness settings
- Module-specific configurations

### `pytest.ini`
Configuration for pytest:
- Test discovery paths
- Coverage settings
- Test markers

## Usage

These configuration files are automatically used by the pre-commit hooks and CI/CD pipeline. You don't need to reference them directly in most cases.

If you want to run the tools manually with these configurations:

```bash
# Flake8
flake8 --config=admin/.flake8

# MyPy
mypy --config-file=admin/mypy.ini

# Pytest
pytest -c admin/pytest.ini
```
