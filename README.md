# fontfinder
**fontfinder is a Python package for finding and installing fonts for Unicode scripts. It's useful
when generating documents that must specify a font family and will be viewed across multiple platforms.**
For now, `fontfinder` mostly locates fonts in the [Google Noto font collection](https://fonts.google.com/noto).

## Docs

See [multiscript.app/fontfinder](https://multiscript.app/fontfinder)

## Examples

```python
```

## Attribution

Parts of this library are derived from code in the FindSystemFontsFilename
library by moi15moi (https://github.com/moi15moi/FindSystemFontsFilename/), under the MIT Licence.

See ACKNOWLEDGEMENTS for more detail.

## Installation

   `pip install fontfinder`

## Build Instructions

Use these instructions if you’re building from the source. `fontfinder` has been developed on Python 3.10, but should
work on other versions as well.

1. `git clone https://github.com/multiscript/fontfinder/`
1. `cd fontfinder`
1. `python3 -m venv venv` (Create a virtual environment.)
   - On Windows: `python -m venv venv`
1. `source venv/bin/activate` (Activate the virtual environment.)
   - In Windows cmd.exe: `venv\Scripts\\activate.bat`
   - In Windows powershell: `.\\venv\Scripts\Activate.ps1` You may first need to run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
1. For development work...
   - `pip install -e .` (Creates an editable local install)
1. ...or to build the package:
   - `pip install build`
   - `python -m build`