- v0.13.0:
  - Fixed bug on Windows where installing or uninstalling fonts could hang.
  - Added FontFinder.is_rtl() method for discovering if a script's text direction is right-to-left.
- v0.12.0:
  - Include pyinstaller hook with the package, so that data files are correctly included if the package is part
    of a frozen app.
- v0.11.0:
  - Fixed bug where FontFinder.find_family_fonts() only returned font info for first family name in the list.
- v0.10.0:
  - Initial release