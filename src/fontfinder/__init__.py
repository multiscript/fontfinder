'''
Analyses the majority Unicode script used in a text string, and locates fonts that can help display that string.
For now, only locates fonts in the Google Noto font collection.
'''
from collections import Counter
import copy
from dataclasses import dataclass, field
from enum import Enum, auto
import json
from pathlib import Path, PurePosixPath
import platform

import requests
import unicodedataplus as udp

from fontfinder.fontinfo import *
from fontfinder.cjk import get_noto_cjk_fonts


MAX_CHARS_TO_ANALYSE: int = 2048
'''Maximum number of characters of a string to analyse for script information.'''

ZH_HANT_USE_HK = False


_DATA_DIR_PATH = Path(__file__, "../data").resolve()
_DATA_DIR_PATH.mkdir(parents=True, exist_ok=True)
_SMALL_UNIHAN_PATH = Path(_DATA_DIR_PATH, "small_unihan.json").resolve()

_known_fonts = None
_small_unihan_data = None


class FontFinder:
    def __init__(self):
        pass

    @property
    def all_unicode_scripts(self):
        return list(udp.property_value_aliases['script'].keys())

    @property
    def all_known_font_scripts(self):
        return sorted(set([info.main_script for info in self.known_fonts]))

    @property
    def scripts_not_covered(self):
        return sorted(set(self.all_unicode_scripts) - set(self.all_known_font_scripts) -
                      set(["Commoon", "Inherited", "Unknown"]))

    @property
    def known_fonts(self):
        if _known_fonts is None:
            self._load_known_fonts()
        return _known_fonts

    def _load_known_fonts(self):
        self._load_noto_fonts()

    def _load_noto_fonts(self):
        global _known_fonts
        if _known_fonts is None:
            noto_data = requests.get("https://notofonts.github.io/noto.json").json()
            noto_font_base_url = "https://cdn.jsdelivr.net/gh/notofonts/notofonts.github.io/"

            # Convert the Noto json data into a flat list of FontFileInfo records, to allow for easier
            # filtering of list.
            _known_fonts = []
            for script_tag, script_data in noto_data.items():
                if script_tag == "latin-greek-cyrillic":
                    script_set = ['latin', 'greek', 'cyrillic']
                    # The Noto data treats these 3 scripts as one, but we duplicate the font info for all 3.
                else:
                    script_set = [script_tag]

                for main_script in script_set:
                    # Make the Noto script formatting match the Unicode script formatting.
                    main_script = main_script.replace('-', '_').title()
                    if main_script == 'Sign_Writing':
                        main_script = 'SignWriting' # Mismatch in Noto / Unicode script name
                    for family_name, family_data in script_data['families'].items():
                        form = FontForm.from_str(family_name)
                        for build, relative_url_list in family_data['files'].items():
                            build = FontBuild.from_str(build)
                            for relative_url in relative_url_list:
                                url = noto_font_base_url + relative_url
                                font_info = FontInfo(main_script=main_script, family_name=family_name, url=url)
                                font_info.set_from_noto_url(url)
                                # Form and build have already been set from the URL, but we can ensure the values are
                                # correct from the other JSON data.
                                font_info.form = form
                                font_info.build = build
                                _known_fonts.append(font_info)
        
        _known_fonts.extend(get_noto_cjk_fonts())
        # _known_fonts.sort()      

    def _load_small_unihan_data(self):
        global _small_unihan_data
        if _small_unihan_data is None:
            with open(_SMALL_UNIHAN_PATH) as small_unihan_file:
                _small_unihan_data = json.load(small_unihan_file)
    
    def get_text_info(self, text: str):
        '''Analyse an initial portion of `text` for the Unicode scripts it uses. Returns a `TextInfo`
        object with the analysis results.

        The number of characters analysed is set by the module attribute `MAX_CHARS_TO_ANALYSE`.

        In setting the `TextInfo.main_script` result, the Unicode script property values `Common`, `Inherited`, and
        `Unknown` are ignored.

        If the resulting `TextInfo.main_script` is `Han`, some basic language detection is performed, and the
        `TextInfo.script_variant` field is set to one of the following language tags:
            For Simplified Chinese:  `zh-Hans`                   
            For Traditional Chinese: `zh-Hant` (or `zh-Hant-HK` if the module attribute `ZH_HANT_USE_HK` is True)
            For Japanese:            `ja`
            For Korean:              `ko`
        '''
        self._load_small_unihan_data()
        script_counter = Counter()
        unihan_counter = Counter()
        for char in text[0:min(len(text), MAX_CHARS_TO_ANALYSE)]:
            script = udp.script(char)
            script_counter[script] += 1
            if char in _small_unihan_data:
                for key in _small_unihan_data[char].keys():
                    unihan_counter[key] += 1
        text_info = TextInfo(script_count=script_counter.most_common())

        ignore_scripts = set(['Common', 'Inherited', 'Unknown'])
        for ignore_script in ignore_scripts:
            del script_counter[ignore_script]

        main_script = script_counter.most_common(1)[0][0]
        script_variant = ""

        if main_script == 'Han':
            # Han script can be used by Chinese, Japanese and Korean texts
            if 'Hangul' in script_counter:
                # If Hangul characters are present, assume it's Korean
                script_variant = 'ko'
            elif 'Hiragana' in script_counter or 'Katakana' in script_counter:
                # If Hirogana or Katakana characters are present, assume it's Japanese
                script_variant = 'ja'
            elif unihan_counter['kSimplifiedVariant'] > unihan_counter['kTraditionalVariant']:
                # Traditional Chinese characters have simplified variants, and vice versa.
                # So if there are more simplified variants than traditional, we likely have traditional text,
                # and vice-versa.
                script_variant = 'zh-Hant-HK' if ZH_HANT_USE_HK else 'zh-Hant'
            else:
                script_variant = 'zh-Hans'

        text_info.main_script=main_script
        text_info.script_variant=script_variant
        return text_info

    def get_installed_families(self):
        if platform.system() == "Darwin":
            import Cocoa
            font_manager = Cocoa.NSFontManager.sharedFontManager()
            installed_families = list(font_manager.availableFonts())
        
        elif platform.system() == "Windows":
            import win32gui

            def enum_font_fam_proc(log_font, text_metric, font_type, installed_families):
                '''Callback for win32gui.EnumFontFamilies()'''
                installed_families.append(log_font.lfFaceName)
                return 1 # A postive return value is needed to continue enumeration
            
            installed_families = []
            hDC = win32gui.GetDC(None) # None for the window handle is acceptable (returns DC for entire screen)
            win32gui.EnumFontFamilies(hDC, None, enum_font_fam_proc, installed_families)
            win32gui.ReleaseDC(None, hDC)
        else:
            raise Exception("Unsupported platform for get_installed_families()")
        
        return sorted(installed_families)

    def get_installed_filenames(self):
        import find_system_fonts_filename
        return find_system_fonts_filename.get_system_fonts_filename()


@dataclass
class TextInfo:
    main_script: str = ""
    '''Name of the most frequently used Unicode script in a piece of text.'''

    script_variant: str = ""
    '''A secondary string to provide extra information when main_script name is insufficient for choosing a font.'''

    script_count: list[tuple[str, int]] = field(default_factory=list)
    '''The raw character counts of each Unicode script value analysed for the text, as a list of tuples.
    Each tuple is of the form `('script', count)`, listed from most-to-least frequent.'''


