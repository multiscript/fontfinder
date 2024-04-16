# Release Process

  1. Update version numbers in `pyproject.toml` and 'CHANGES.md`
  1. If first build: `pip install build`
  1. Remove old `dist/` directory
  1. `python -m build`
  1. If first release: `pip install twine`
  1. `twine upload dist/*`
     - Username: `__token__`
     - Password: (supply release token key)
  1. Check release is fine on PyPi
  1. Create a new release tag on `main`, named `vX.Y.Z`. Include the contents of `dist/*` as assets.
