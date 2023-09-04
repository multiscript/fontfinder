'''
Analyses the majority Unicode script used in a text string, and locates fonts that can help display that string.
For now, only locates fonts in the Google Noto font collection.
'''
from collections import Counter
from dataclasses import dataclass, field
import json
from pathlib import Path
import platform

import unicodedataplus as udp

from fontfinder.fontinfo import *


MAX_CHARS_TO_ANALYSE: int = 2048
'''Maximum number of characters of a string to analyse for script information.'''

ZH_HANT_USE_HK = False
'''If True, `FontFinder.get_text_info()` selects Hong Kong rather than Taiwanese fonts for Traditional Chinese
Script.'''

_DATA_DIR_PATH = Path(__file__, "../data").resolve()
'''Path to font data'''
_DATA_DIR_PATH.mkdir(parents=True, exist_ok=True)

_SMALL_UNIHAN_PATH = Path(_DATA_DIR_PATH, "small_unihan.json").resolve()
'''Path to subset of Unihan data.'''

# We wait until now to import Noto data so that data path constants above are set.
from fontfinder import noto 


class FontFinder:
    '''FontFinder object exposes this package's functionality.'''
    def __init__(self):
        self._all_known_fonts = None
        self._small_unihan_data_private = None
        self.font_family_prefs = {}
        self.set_default_prefs()

    @property
    def all_unicode_scripts(self):
        return list(udp.property_value_aliases['script'].keys())

    @property
    def all_known_font_scripts(self):
        return sorted(set([info.main_script for info in self.known_fonts()]))

    @property
    def scripts_not_covered(self):
        return sorted(set(self.all_unicode_scripts) - set(self.all_known_font_scripts) -
                      set(["Common", "Inherited", "Unknown"]))

    def known_fonts(self, filter_func = None):
        # Even though noto.get_noto_fonts() can filter on the fly, for now we choose to optimise for speed, rather
        # than memory, by caching the full list of font_infos in memory.
        if self._all_known_fonts is None:
            self._all_known_fonts = noto.get_noto_fonts()
        return [font_info for font_info in self._all_known_fonts if (filter_func is None or filter_func(font_info))]

    @property
    def _small_unihan_data(self):
        if self._small_unihan_data_private is None:
            with open(_SMALL_UNIHAN_PATH) as small_unihan_file:
                self._small_unihan_data_private = json.load(small_unihan_file)
        return self._small_unihan_data_private
    
    def get_text_info(self, text: str):
        '''Analyse an initial portion of `text` for the Unicode scripts it uses. Returns a `TextInfo`
        object with the results.

        The number of characters analysed is set by the module attribute `MAX_CHARS_TO_ANALYSE`.

        The attributes of the `TextInfo` result object are set as follows:

            `main_script`: name of the most-frequently-used Unicode script in `text`.

            `script_variant`: a secondary string used when the value of `main_script` is insufficient for choosing
                              an appropriate font.

            `emoji_count`: count of characters who have either the Emoji Presentation property or the
                           Extended_Pictographic property set (independant of script).

            `script_count`: a collections.Counter of the count of each Unicode script in the text. The keys are the
                            string names of each script that appears in the text (including `Common`, `Inherited`
                            and `Unknown`).

        In calculating `main_script`, the script values `Common`, `Inherited`, and `Unknown` are
        ignored. However if `emoji_count` is larger then the rest of the script counts, then `main_script' is set to
        `Common` and `script_variant` is set to `Emoji`. (Most emoji characters have a script value of `Common`.)
        
        If `main_script` is `Han`, some basic language detection is performed, and the `script_variant` is set to
        one of the following language tags:
            For Simplified Chinese:  `zh-Hans`                   
            For Traditional Chinese: `zh-Hant` (or `zh-Hant-HK` if the module attribute `ZH_HANT_USE_HK` is True)
            For Japanese:            `ja`
            For Korean:              `ko`
        '''
        # Do the counting
        script_count = Counter()
        unihan_counter = Counter()
        emoji_count = 0
        for char in text[0:min(len(text), MAX_CHARS_TO_ANALYSE)]:
            script_count[udp.script(char)] += 1
            if udp.is_emoji_presentation(char) or udp.is_extended_pictographic(char):
                emoji_count += 1
            if char in self._small_unihan_data:
                for key in self._small_unihan_data[char].keys():
                    unihan_counter[key] += 1
        
        # Determine main_script and script_variant
        non_generic_count = script_count.copy()
        generic_scripts = ['Common', 'Inherited', 'Unknown']
        for generic_script in generic_scripts:
            del non_generic_count[generic_script]

        if len(non_generic_count) > 0:
            main_script = non_generic_count.most_common(1)[0][0]
            script_variant = ""
        else:
            main_script = ""
            script_variant = ""

        # Handle emoji
        if (len(non_generic_count) == 0 and emoji_count > 0) or emoji_count > non_generic_count.most_common(1)[0][1]:
            main_script = "Common"
            script_variant = "Emoji"

        # Handle Han script
        if main_script == 'Han':
            # Han script can be used by Chinese, Japanese and Korean texts
            if 'Hangul' in script_count:
                # If Hangul characters are present, assume it's Korean
                script_variant = 'ko'
            elif 'Hiragana' in script_count or 'Katakana' in script_count:
                # If Hirogana or Katakana characters are present, assume it's Japanese
                script_variant = 'ja'
            elif unihan_counter['kSimplifiedVariant'] > unihan_counter['kTraditionalVariant']:
                # Traditional Chinese characters have simplified variants, and vice versa.
                # So if there are more simplified variants than traditional, we likely have traditional text,
                # and vice-versa.
                script_variant = 'zh-Hant-HK' if ZH_HANT_USE_HK else 'zh-Hant'
            else:
                script_variant = 'zh-Hans'

        return TextInfo(main_script=main_script, script_variant=script_variant, emoji_count=emoji_count,
                        script_count=script_count)

    def set_default_prefs(self):
        self.font_info_pref_order = list(dataclasses.asdict(FontInfo()).keys())
        self.font_info_prefs = dataclasses.asdict(FontInfo())
        self.font_family_prefs[("Arabic", "")] = "Noto Naskh Arabic"

    def apply_prefs(self, font_info_iterable):
        old_list = font_info_iterable
        # Font preferences are lists of preferred values for each attribute of FontInfo.
        # We filter the list of FontInfos one attribute at a time, so to start with we
        # loop over each attribute of FontInfo, in the preferred order.
        for font_info_attr_name in self.font_info_pref_order:
            # Aggregate each possible value for the attribute in the list of FontInfos
            aggregate = FontInfo.aggregate(old_list)
            # Begin our new filtered list
            new_list = []
            # We only filter on the attribute if there is more than one value for the attribute in the list
            if len(aggregate[font_info_attr_name]) > 1:
                # Loop over each FontInfo in the old list
                for font_info in old_list:
                    # Loop over each preferred value for the attribute
                    for pref_value in self.font_family_prefs[font_info_attr_name]:
                        # If this font_info has the preferred value, it's included in the new list
                        if getattr(font_info, font_info_attr_name) == pref_value:                
                            new_list.append(font_info)
                            break
            else:
                # There was only one value for this attribute for the FontInfos in the list, so we skip filtering.
                pass
            old_list = new_list
        return new_list

    def find_font_family(self, text_or_info):
        if isinstance(text_or_info, str):
            text_info = self.get_text_info(text_or_info)
        else:
            text_info = text_or_info

        font_family_pref_key = (text_info.main_script, text_info.script_variant)
        if font_family_pref_key in self.font_family_prefs:
            family_name = self.font_family_prefs[font_family_pref_key]
        else:
            family_name = self.find_font_families(text_info)[0]
        return family_name

    def find_font_families(self, text_or_info):
        if isinstance(text_or_info, str):
            text_info = self.get_text_info(text_or_info)
        else:
            text_info = text_or_info
        
        font_infos = self.known_fonts(lambda font_info: font_info.main_script == text_info.main_script and \
                                                        font_info.script_variant == text_info.script_variant)
        # We use a dictionary as a set that preserves insertion order
        family_names = {font_info.family_name: 1 for font_info in font_infos}
        return list(family_names.keys())

    def find_font_info(self, family_name_or_iterable):
        if isinstance(family_name_or_iterable, str):
            family_name_or_iterable = [family_name_or_iterable]
        family_names = family_name_or_iterable

    def _OLD_get_installed_families(self):
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

    def _OLD_get_installed_filenames(self):
        import find_system_fonts_filename
        return find_system_fonts_filename.get_system_fonts_filename()


@dataclass
class TextInfo:
    main_script: str = ""
    '''Name of the most frequently used Unicode script in a piece of text.'''

    script_variant: str = ""
    '''a secondary string used when the value of `main_script` is insufficient for choosing an appropriate font.'''

    emoji_count: int = 0
    '''Count of characters who have either the Emoji Presentation property or the Extended_Pictographic property set
    (independant of script).'''

    script_count: Counter = field(default_factory=Counter)
    '''A collections.Counter of the count of each Unicode script in the text. The keys are the string names of
    each script that appears in the text.'''
    


