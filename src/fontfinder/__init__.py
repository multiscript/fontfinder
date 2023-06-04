'''
Analyses the majority Unicode script used in a text string, and locates fonts that can help display that string.
For now, only locates fonts in the Google Noto font collection.
'''
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
import platform

import requests
import unicodedataplus as udp

MAX_CHARS_TO_ANALYSE: int = 2048
'''Maximum number of characters of a string to analyse for script information.'''

_DATA_DIR_PATH = Path(__file__, "../data").resolve()
_DATA_DIR_PATH.mkdir(parents=True, exist_ok=True)
_SMALL_UNIHAN_PATH = Path(_DATA_DIR_PATH, "small_unihan.json").resolve()

_known_fonts = None
_small_unihan_data = None

class FontFinder:
    def __init__(self):
        pass
    
    def _load_known_fonts(self):
        global _known_fonts
        if _known_fonts is None:
            noto_data = requests.get("https://notofonts.github.io/noto.json").json()

            # Convert the Noto json data into a flat list of FontFileInfo records, to allow for easier
            # filtering of list.
            _known_fonts = []
            for script_tag, script_data in noto_data.items():
                if script_tag == "latin-greek-cyrillic":
                    script_set = ['latin', 'greek', 'cyrillic']
                    # The Noto data treats these 3 scripts as one, but we duplicate the font info for all 3.
                else:
                    script_set = [script_tag]

                for script in script_set:
                    # Make the Noto script formatting match the Unicode script formatting.
                    script = script.replace('-', '_').title()

                    for family, family_data in script_data['families'].items():
                        if FontSerif.SANS_SERIF.value.casefold() in family.casefold():
                            serif = FontSerif.SANS_SERIF
                        else:
                            serif = FontSerif.SERIF

                        for build, relative_url_list in family_data['files'].items():
                            build = FontBuild(build.title())
                            for relative_url in relative_url_list:
                                format = FontFormat(relative_url[-3:].upper())

                                width = FontWidth.NORMAL # Default
                                for width_item in FontWidth.search_order():
                                    if width_item.value.casefold() in relative_url.casefold():
                                        width = width_item

                                weight = FontWeight.REGULAR # Default
                                for weight_item in FontWeight.search_order():
                                    if weight_item.value.casefold() in relative_url.casefold():
                                        weight = weight_item

                                style = FontStyle.UPRIGHT # Default
                                for style_item in FontStyle.search_order():
                                    if style_item.value.casefold() in relative_url.casefold():
                                        style = style_item

                                font_file_info = FontFileInfo(script, family, serif, build, width, weight, style,
                                                            format, relative_url)
                            _known_fonts.append(font_file_info)

    def _load_small_unihan_data(self):
        global _small_unihan_data
        if _small_unihan_data is None:
            with open(_SMALL_UNIHAN_PATH) as small_unihan_file:
                _small_unihan_data = json.load(small_unihan_file)
    
    def get_text_info(self, text: str):
        '''Analyse an initial portion of `text` for the Unicode scripts it uses. Returns a `TextInfo`
        object with the analysis results.

        Only the first `MAX_CHARS_TO_ANALYSE` characters are analysed.
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

        if main_script == 'Han':
            # Han script can be used by Chinese, Japanese and Korean texts
            if 'Hangul' in script_counter:
                # If Hangul characters are present, assume it's Korean
                main_script = 'Korean'
            elif 'Hiragana' in script_counter or 'Katakana' in script_counter:
                # If Hirogana or Katakana characters are present, assume it's Japanese
                main_script = 'Japanese'
            elif unihan_counter['kSimplifiedVariant'] > unihan_counter['kTraditionalVariant']:
                # Traditional Chinese characters have simplified variants, and vice versa.
                # So if there are more simplified variants than traditional, we likely have traditional text,
                # and vice-versa.
                main_script = 'Chinese (Traditional)'
            else:
                main_script = 'Chinese (Simplified)'
        elif main_script == 'Hangul':
            main_script = 'Korean'
        elif main_script in ['Hiragana', 'Katakana']:
            main_script = 'Japanese'

        text_info.main_script=main_script
        return text_info

    def known_fonts(self):
        self._load_known_fonts()
        return _known_fonts

    def get_installed_families(self):
        if platform.system() == "Darwin":
            import Cocoa
            font_manager = Cocoa.NSFontManager.sharedFontManager()
            installed_families = list(font_manager.availableFontFamilies())
        
        elif platform.system() == "Windows":
            import win32gui

            def enum_font_fam_proc(log_font, text_metric, font_type, installed_families):
                installed_families.append(log_font.lfFaceName)
                return 1 # A postive return value is needed to continue enumeration
            
            installed_families = []
            hDC = win32gui.GetDC(None) # None as window handle is acceptable (gives DC for entire screen)
            win32gui.EnumFontFamilies(hDC, None, enum_font_fam_proc, installed_families)
            win32gui.ReleaseDC(None, hDC)
        else:
            raise Exception("Unsupport platform for get_installed_families()")
        
        return sorted(installed_families)

@dataclass
class TextInfo:
    main_script: str = None
    '''The most frequent Unicode script used in a piece of text, subject to the following conditions:
    
    The Unicode script property values `Common`, `Inherited`, and `Unknown` are ignored. If the most frequently used
    script is one of `Han`, `Hangul`, `Hiragana` or `Katakana`, this field is set to one of the following strings
    instead, representing an estimate of the language used in the text:
        `Chinese (Traditional)`, `Chinese (Simplified)`, `Japanese`, `Korean`
    '''
    script_count: list[tuple[str, int]] = field(default_factory=list)
    '''The raw character counts of each Unicode script value analysed for the text, as a list of tuples.
    Each tuple is of the form `('script', count)`, listed from most-to-least frequent.'''


@dataclass
class FontFileInfo:
    script: str = ""
    '''Primary Unicode script covered by the font.'''

    family: str = ""
    '''Font family name.'''

    serif: 'FontSerif' = ""

    build: 'FontBuild' = ""

    width: 'FontWidth' = ""
    
    weight: 'FontWeight' = ""

    style: 'FontStyle' = ""

    format: 'FontFormat' = ""
    
    url: str = ""
    '''URL download source for the font.'''


class FontSerif(Enum):
    UNKNOWN     = ""
    SERIF       = "Serif"
    SANS_SERIF  = "Sans"

    @classmethod
    def search_order(cls):
        return sorted([item for item in cls if item not in [FontSerif.UNKNOWN]],
                      key=lambda item: len(item.value))


class FontBuild(Enum):
    UNHINTED    = "Unhinted"
    HINTED      = "Hinted"
    FULL        = "Full"

    @classmethod
    def search_order(cls):
        return sorted([item for item in cls], key=lambda item: len(item.value))


class FontWidth(Enum):
    NORMAL      = ""
    VAR_WIDTH   = "wdth"
    EXTRA_COND  = "ExtraCondensed"
    CONDENSED   = "Condensed"
    SEMI_COND   = "SemiCondensed"

    @classmethod
    def search_order(cls):
        return sorted([item for item in cls if item not in [FontWidth.NORMAL]],
                      key=lambda item: len(item.value))


class FontWeight(Enum):
    REGULAR     = "Regular"
    VAR_WEIGHT  = "wght"
    EXTRA_LIGHT = "ExtraLight"
    LIGHT       = "Light"
    THIN        = "Thin"
    MEDIUM      = "Medium"
    SEMI_BOLD   = "SemiBold"
    BOLD        = "Bold"
    EXTRA_BOLD  = "ExtraBold"
    BLACK       = "Black"

    @classmethod
    def search_order(cls):
        return sorted([item for item in cls if item not in [FontWeight.REGULAR]],
                      key=lambda item: len(item.value))


class FontStyle(Enum):
    UPRIGHT     = ""
    ITALIC      = "Italic"
 
    @classmethod
    def search_order(cls):
        return sorted([item for item in cls if item not in [FontStyle.UPRIGHT]],
                      key=lambda item: len(item.value))


class FontFormat(Enum):
    UNSET       = ""
    OTF         = "OTF"
    OTC         = "OTC"
    TTF         = "TTF"

    @classmethod
    def search_order(cls):
        return sorted([item for item in cls if item not in [FontFormat.UNSET]],
                      key=lambda item: len(item.value))
