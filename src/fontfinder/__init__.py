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
import fontfinder.mac


# TODO: Test finding font family members.
# TODO: Ensure we return at least one font family name for every script.
# TODO: Ensure we return font_infos for every script.

MAX_CHARS_TO_ANALYSE: int = 2048
'''Maximum number of characters of a string to analyse for script information.'''

ZH_HANT_USE_HK = False
'''If True, `FontFinder.get_text_info()` selects Hong Kong rather than Taiwanese fonts for Traditional Chinese
Script.'''

_DATA_DIR_PATH = Path(__file__, "../data").resolve()
'''Path to font data'''
_DATA_DIR_PATH.mkdir(parents=True, exist_ok=True)

_SMALL_UNIHAN_PATH = Path(_DATA_DIR_PATH, "small_unihan.json").resolve()
'''Path to subset of Unihan data neede for CJK font selection.'''

ANY_SCRIPT = object() # Sentinel for preference matching on any script

# We wait until now to import Noto data so that data path constants above are set.
from fontfinder import noto 


def any_of(attr_name, collection):
    '''A filter factory. Returns a filter function that takes a single argument `obj` and returns True
    if `obj.attr_name` is in `collection`, else False.
    '''
    def filter(obj):
        return getattr(obj, attr_name) in collection
    return filter

def none_of(attr_name, collection):
    '''A filter factory. Returns a filter function that takes a single argument `obj` and returns True
    if `obj.attr_name` is not in `collection`, else False.
    '''
    def filter(obj):
        return getattr(obj, attr_name) not in collection
    return filter
    

class FontFinder:
    '''FontFinder object exposes this package's functionality.'''
    def __init__(self):
        self._all_known_fonts = None
        self._small_unihan_data_private = None
        self.font_family_prefs = {}
        self.family_member_prefs = {}
        self.set_default_prefs()

    def known_fonts(self, filter_func = None):
        '''Returns a list of FontInfo objects for all fonts known by this library.'''
        # Even though noto.get_noto_fonts() can filter on the fly, for now we choose to optimise for speed, rather
        # than memory, by caching the full list of font_infos in memory.
        if self._all_known_fonts is None:
            self._all_known_fonts = noto.get_noto_fonts()
        return [font_info for font_info in self._all_known_fonts if (filter_func is None or filter_func(font_info))]

    def known_scripts(self, filter_func = None):
        '''Returns a list of the `main_script` values for all the fonts known by this library.'''
        return sorted(set([info.main_script for info in self.known_fonts(filter_func)]))

    def known_script_variants(self, filter_func = None):
        '''Returns a list of `(main_script, script_variant)` tuples for all the fonts known by this library.'''
        # Use a dictionary as an ordered set
        return list({(info.main_script, info.script_variant): 1 for info in self.known_fonts(filter_func)}.keys())

    def all_unicode_scripts(self):
        '''Returns a list of all script values in the Unicode standard.'''
        return list(udp.property_value_aliases['script'].keys())

    def scripts_not_known(self):
        '''Returns a list of all the Unicode script values not supported by the fonts known to this library.'''
        return sorted(set(self.all_unicode_scripts()) - set(self.known_scripts()) -
                      set(["Common", "Inherited", "Unknown"]))

    @property
    def _small_unihan_data(self):
        if self._small_unihan_data_private is None:
            with open(_SMALL_UNIHAN_PATH) as small_unihan_file:
                self._small_unihan_data_private = json.load(small_unihan_file)
        return self._small_unihan_data_private
    
    def analyse(self, text: str):
        '''Analyse an initial portion of `text` for the Unicode scripts it uses. Returns a `TextInfo`
        object with the results.

        The number of characters analysed is set by the module attribute `MAX_CHARS_TO_ANALYSE`.

        The attributes of the `TextInfo` result object are set as follows:

            `main_script`: name of the most-frequently-used Unicode script in `text`.

            `script_variant`: a secondary string used when the value of `main_script` is insufficient for choosing
                              an appropriate font.

            `emoji_count`:    count of characters who have either the Emoji Presentation property or the
                              Extended_Pictographic property set (independant of script).

            `script_count`:   a collections.Counter of the count of each Unicode script in the text. The keys are
                              the string names of each script that appears in the text (including `Common`,
                              `Inherited` and `Unknown`).

        In calculating `main_script`, the script values `Common`, `Inherited`, and `Unknown` are
        ignored. However if `emoji_count` is larger than the rest of the script counts, then `main_script' is set to
        `Common` and `script_variant` is set to `Emoji`. (Most emoji characters have a Unicode script value of
        `Common`.)
        
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
        '''Sets the default font preferences. These can be modified either by overriding this method, or by
        editing the `font_family_prefs` and `family_member_prefs` attributes.
        
        Font preferences are dictionaries of lists of filter functions. The keys are either `ANY_SCRIPT` or tuples of
        (main_script, script_variant). The values are lists of filter functions. The filters are usually created
        using the filter factories `any_of()` or `none_of()`, but can be any custom filter function that takes a
        `FontInfo` object and returns True if the object should be included in the filtered list.
        '''
        self.font_family_prefs[("Arabic", "")] = [any_of("family_name", ["Noto Naskh Arabic"]),
                                                 ]
        self.font_family_prefs[ANY_SCRIPT] = [any_of("form", [FontForm.SANS_SERIF]),
                                             ]
        self.family_member_prefs[ANY_SCRIPT] = [none_of("width", [FontWidth.VARIABLE]),
                                                none_of("weight", [FontWidth.VARIABLE]),
                                                any_of("build", [FontBuild.FULL]),
                                                any_of("format", [FontFormat.OTF]),
                                                any_of("format", [FontFormat.TTF]),
                                                any_of("format", [FontFormat.OTC]),
                                               ]

    def find_font_families(self, str_or_text_info):
        '''Returns a list of the family names (strings) of all fonts (known to the library) that are suitable for
        displaying some text.
        
        `str_or_text_info` should either be the string of text itself, or a TextInfo object returned by
        `analyse()`.
        '''
        font_infos = self._text_info_to_font_infos(str_or_text_info)
        # We use a dictionary as a set that preserves insertion order, to return families in their original order.
        family_names = {font_info.family_name: 1 for font_info in font_infos}
        return list(family_names.keys())

    def find_font_family(self, str_or_text_info):
        '''Returns the family name (a string) for the font family considered most-suitable for displaying some text.
        "Most-suitable" is determined by the filter functions in the preference attribute `font_family_prefs`.
        If, after applying these filters, more than one family remains, the first family is selected.
        
        `str_or_text_info` should either be the string of text itself, or a TextInfo object returned by
        `analyse()`.
        '''
        font_infos = self._text_info_to_font_infos(str_or_text_info)
        if len(font_infos) == 0:
            return None
        count_func = lambda font_infos: len({font_info.family_name for font_info in font_infos})
        font_infos = self._apply_pref_dict(font_infos[0].main_script, font_infos[0].script_variant,
                                           self.font_family_prefs, count_func, font_infos)
        family_name = font_infos[0].family_name
        return family_name

    def find_family_members(self, family_name_or_names):
        '''Returns a list of FontInfo objects for the font family name or names in `family_name_or_names`.
        The list is filtered according to the filter functions in the preference attribute `family_member_prefs`.
         
        `family_name_or_names` can be the string of a single font family names, or a list of strings of font family
        names.
        '''
        family_names = family_name_or_names
        if isinstance(family_names, str):
            family_names = [family_names]
        font_infos = self.known_fonts(lambda font_info: font_info.family_name in family_names)
        count_func = len
        font_infos = self._apply_pref_dict(font_infos[0].main_script, font_infos[0].script_variant,
                                           self.family_member_prefs, count_func, font_infos)
        return font_infos

    def _text_info_to_font_infos(self, str_or_text_info):
        if isinstance(str_or_text_info, str):
            text_info = self.analyse(str_or_text_info)
        else:
            text_info = str_or_text_info
        font_infos = self.known_fonts(lambda font_info: font_info.main_script == text_info.main_script and \
                                                        font_info.script_variant == text_info.script_variant)
        return font_infos

    def _apply_pref_dict(self, main_script, script_variant, pref_dict, count_func, font_infos):
        # Preferences for particular scripts are applied before preferences for any script
        pref_keys = [(main_script, script_variant), ANY_SCRIPT]
        for pref_key in pref_keys:
            if pref_key in pref_dict:
                font_infos = self._apply_pref_filters(pref_dict[pref_key], count_func, font_infos)
        return font_infos

    def _apply_pref_filters(self, filter_funcs, count_func, font_infos):
        cur_list = font_infos
        count = count_func(cur_list)
        # print(f"Initial ({count})")
        # print([info.url for info in font_infos])
        # print()
        if count < 2 or len(filter_funcs) == 0:
            # We actually don't need to filter.
            return cur_list

        print("After each filter func")
        for filter_func in filter_funcs:
            new_list = [font_info for font_info in cur_list if filter_func(font_info)]
            count = count_func(new_list)
            # print(count)
            # print([info.url for info in new_list])
            # print()
            if count == 0:
                # This preference was too restrictive, so we ignore it by not updating cur_list
                pass
            elif count == 1:
                # Perfect! Stop filtering
                cur_list = new_list
                break
            else:
                # Keep filtering
                cur_list = new_list
        return cur_list

    def all_installed_families(self):
        '''Returns a list of strings of the family names of all fonts installed on the system.
        '''
        if platform.system() == "Darwin":
            all_installed_families = fontfinder.mac.all_installed_families()
        else:
            raise Exception("Unsupported platform for get_installed_families()")
        
        return sorted(all_installed_families)

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
    


