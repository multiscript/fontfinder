from fontfinder import FontFinder
ff = FontFinder()
text = 'الشمس (رمزها: ☉) هي النجم المركزي للمجموعة الشمسية.' # From Arabic Wikipedia article about the Sun
ff.analyse(text)
known_families = ff.find_families(text)
print(known_families)
preferred_family = ff.find_family(text)
print(preferred_family)
print(ff.installed_families(preferred_family))
family_fonts = ff.find_family_fonts(preferred_family)
print([font_info.postscript_name for font_info in family_fonts])
from tempfile import TemporaryDirectory
tempdir = TemporaryDirectory()
fonts_for_download = ff.find_family_fonts_to_download(preferred_family)
fonts_for_install = ff.download_fonts(fonts_for_download, tempdir.name)
ff.install_fonts(fonts_for_install)
print(ff.installed_families(preferred_family))
ff.uninstall_fonts(fonts_for_install)
print(ff.installed_families(preferred_family))
tempdir.cleanup()


