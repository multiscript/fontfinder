'''
## Overview
**fontfinder is a Python package for finding and installing fonts that can display the majority Unicode script used
in a text string.** For now, `fontfinder` mostly locates fonts in the
[Google Noto font collection](https://fonts.google.com/noto).

Most functionality is provided by instantiating the `FontFinder` class.

## Examples

Coming soon.

## Top-Level Objects
'''
from collections import Counter
import json
from pathlib import Path
import tempfile
from typing import Iterable

import requests
import unicodedataplus as udp

from fontfinder.data_classes import TextInfo
from fontfinder.filters import *
from fontfinder.data_classes import *
from fontfinder import _platforms


_DATA_DIR_PATH = Path(__file__, "../data").resolve()
'''Path to font data'''
_DATA_DIR_PATH.mkdir(parents=True, exist_ok=True)

_SMALL_UNIHAN_PATH = Path(_DATA_DIR_PATH, "small_unihan.json").resolve()
'''Path to subset of Unihan data neede for CJK font selection.'''

# We wait until now to import Noto data so that data path constants above are set.
from fontfinder import noto 


class FontFinder:
    '''Main class for accessing this library's functionality.'''
    def __init__(self):
        self._all_known_fonts = None
        self._small_unihan_data_private = None
        
        self.max_analyse_chars: int = 2048
        '''Maximum number of characters examined by `FontFinder.analyse().'''
        
        self.zh_hant_use_hk = False
        '''If True, `FontFinder.analyse()` selects Hong Kong rather than Taiwanese fonts for Traditional
        Chinese script.'''

        self.font_family_prefs = {}
        '''Font preferences for selecting a single font-family for some text. This attribute is a dictionary of lists
        of filter functions. See `set_prefs()` for more info.'''

        self.family_member_prefs = {}
        '''Font preferences for selecting the members of a given font-family. This attribute is a dictionary of lists
        of filter functions. See `set_prefs()` for more info.'''

        self.set_prefs()

    def set_prefs(self) -> None:
        '''Sets the font preferences. See the source code for this method to examine the built-in preferences
        that `fontfinder` uses 'out-of-the-box'. These can be replaced either by overriding this method, or editing
        the `font_family_prefs` and `family_member_prefs` instance attributes.
        
        Font preferences are dictionaries of lists of filter functions. The dictionary keys are one of:
        - the`fontfinder.ANY_SCRIPT` object. Preferences under this key will apply to any script.
        - A tuple of `(main_script, script_variant)`. Preferences under these keys will only apply to that particula
          script and variant combination.
        
        The dictionary values are lists of filter functions. The filters are usually created
        using the filter factories in the `fontfinder.filters` module. However, any custom filter function can be used
        that takes a single `fontfinder.data_classes.FontInfo` argument and returns True if the object should be included
        in the filtered list.

        Preferences for particular script/variant combinations are applied before preferences for `ANY_SCRIPT`.
        If applying a preference would result in all remaining fonts being excluded, the preference is ignored.

        Some example preferences:
        ```python
        # For Arabic, prefer the more traditional Naskh form
        self.font_family_prefs[("Arabic", "")] = [any_of("family_name", ["Noto Naskh Arabic"])]

        # Prefer sans-serif fonts, and exclude mono, display and UI forms where possible.
        self.font_family_prefs[ANY_SCRIPT] = [any_of("form",     [FontForm.SANS_SERIF]),
                                              none_of_in("tags", [FontTag.MONO, FontTag.DISPLAY, FontTag.UI])]
        ```
        '''
        # For Adlam, prefer joined to unjoined.
        self.font_family_prefs[("Adlam", "")] = [any_of("family_name", ["Noto Sans Adlam"])]
        # For Arabic, prefer the more traditional Naskh form
        self.font_family_prefs[("Arabic", "")] = [any_of("family_name", ["Noto Naskh Arabic"])]
        # For Hebrew, prefer the more traditional Serif form
        self.font_family_prefs[("Hebrew", "")] = [any_of("family_name", ["Noto Serif Hebrew"])]
        # For Khitan Small Script, prefer Noto Serif Khitan Small Script, as the purpose of the other fonts isn't clear
        self.font_family_prefs[("Khitan_Small_Script", "")] = [any_of("family_name",
                                                                     ["Noto Serif Khitan Small Script"])]
        # For Lao, prefer more traidtional looped fonts
        self.font_family_prefs[("Lao", "")] = [any_of_str_in("family_name", ["Looped"])]
        # For Nko, prefer Noto Sans NKo to unjoined
        self.font_family_prefs[("Nko", "")] = [any_of("family_name", ["Noto Sans NKo"])]
        # For Nushu, prefer Noto Sans Nushu as it is better for smaller font sizes
        self.font_family_prefs[("Nushu", "")] = [any_of("family_name", ["Noto Sans Nushu"])]
        # For Tamil, don't use the Supplement font
        self.font_family_prefs[("Tamil", "")] = [none_of_str_in("family_name", ["Supplement"])]
        # For Thai, prefer more traidtional looped fonts, and Noto Sans Thai Looped in particular
        self.font_family_prefs[("Thai", "")] = [any_of("family_name", ["Noto Sans Thai Looped"])]
        # Prefer sans-serif fonts, and exclude mono, display and UI forms where possible.
        self.font_family_prefs[ANY_SCRIPT] = [any_of("form",        [FontForm.SANS_SERIF]),
                                              none_of_in("tags",    [FontTag.MONO, FontTag.DISPLAY, FontTag.UI])]
        self.family_member_prefs[ANY_SCRIPT] = [none_of("width",    [FontWidth.VARIABLE]),
                                                none_of("weight",   [FontWidth.VARIABLE]),
                                                none_of_in("tags",  [FontTag.MONO, FontTag.DISPLAY, FontTag.UI]),
                                                any_of("build",     [FontBuild.FULL]),
                                                any_of("build",     [FontBuild.HINTED]),
                                                any_of("format",    [FontFormat.OTF]),
                                                any_of("format",    [FontFormat.TTF]),
                                                any_of("format",    [FontFormat.OTC]),
                                               ]

    def analyse(self, text: str) -> TextInfo:
        '''Analyse an initial portion of `text` for the Unicode scripts it uses. Returns a
        `fontfinder.data_classes.TextInfo` object with the results.

        The number of characters analysed is set by the instance attribute `max_analyse_chars`.

        The attributes of the `TextInfo` result object are set as follows:
        - `main_script`:    Name of the most-frequently-used Unicode script in `text`. This is the long Unicode
                            script value (known as a property value alias), rather than the short 4-character
                            script code.

        - `script_variant`: A secondary string used when the value of `main_script` is insufficient for choosing
                            an appropriate font. This is not a Unicode property, but a scheme only used by
                            `fontfinder`. See `FontFinder.analyse()` for examples.

        - `emoji_count`:    Count of characters who have either the Emoji Presentation property or the
                            Extended_Pictographic property set (independent of script).

        - `script_count`:   A [collections.Counter](https://docs.python.org/3/library/collections.html#collections.Counter)
                            of the count of each Unicode script in the text. The keys are the string names of each
                            script that appears in the text (including `Common`, `Inherited` and `Unknown`).

        In calculating `main_script`, the script values `Common`, `Inherited`, and `Unknown` are
        ignored. However if `emoji_count` is larger than the rest of the script counts, then `main_script` is set to
        `Common` and `script_variant` is set to `Emoji`. (Most emoji characters have a Unicode script value of
        `Common`.)
        
        If `main_script` is `Han`, some basic language detection is performed, and the `script_variant` is set to
        one of the following language tags:
        - For Simplified Chinese:  `zh-Hans`                   
        - For Traditional Chinese: `zh-Hant` (or `zh-Hant-HK` if the instance attribute `zh_hant_use_hk` is True)
        - For Japanese:            `ja`
        - For Korean:              `ko`
        '''
        # Do the counting
        script_count = Counter()
        unihan_counter = Counter()
        emoji_count = 0
        for char in text[0:min(len(text), self.max_analyse_chars)]:
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
                script_variant = 'zh-Hant-HK' if self.zh_hant_use_hk else 'zh-Hant'
            else:
                script_variant = 'zh-Hans'

        return TextInfo(main_script=main_script, script_variant=script_variant, emoji_count=emoji_count,
                        script_count=script_count)

    def find_font_families(self, str_or_text_info: str | TextInfo) -> list[str]:
        '''Returns a list of the family names (strings) of all fonts known to the library that are suitable for
        displaying some text. No font family preferences are applied.
        
        `str_or_text_info` should either be the text string itself, or a `TextInfo` object returned by `analyse()`.
        '''
        font_infos = self._text_info_to_font_infos(str_or_text_info)
        # We use a dictionary as a set that preserves insertion order, to return families in their original order.
        family_names = {font_info.family_name: 1 for font_info in font_infos}
        return list(family_names.keys())

    def find_font_family(self, str_or_text_info: str | TextInfo) -> str:
        '''Returns the family name (a string) of the single font family considered most-suitable for
        `str_or_text_info`. "Most-suitable" is determined applying the filter functions in `font_family_prefs`.
        If, after applying these filters, more than one family remains, the first family is returned.
        
        `str_or_text_info` should either be the text string itself, or a `TextInfo` object returned by `analyse()`.
        '''
        font_infos = self._text_info_to_font_infos(str_or_text_info)
        if len(font_infos) == 0:
            return None
        count_func = lambda font_infos: len({font_info.family_name for font_info in font_infos})
        font_infos = self._apply_pref_dict(font_infos[0].main_script, font_infos[0].script_variant,
                                           self.font_family_prefs, count_func, font_infos)
        family_name = font_infos[0].family_name
        return family_name

    def find_family_members_to_install(self, family_name_or_names: str | Iterable[str]) -> list[FontInfo]:
        '''Returns a list of FontInfo objects for any of the font families in `family_name_or_names` that are not
        currently installed. The list is filtered according to the filter functions in the preference attribute
        `family_member_prefs`.

        `family_name_or_names` can be the string of a single font family names, or a list of strings of font family
        names.
        '''
        family_names = self.not_installed_families(family_name_or_names)
        return self.find_family_members(family_names)

    def find_family_members(self, family_name_or_names: str | Iterable[str],
                            main_script:str = None, script_variant:str = None) -> list[FontInfo]:
        '''Returns a list of FontInfo objects for the font family name or names in `family_name_or_names`.
        The list is filtered according to the filter functions in the preference attribute `family_member_prefs`.
         
        `family_name_or_names` can be the string of a single font family names, or a list of strings of font family
        names. `main_script` and `script_variant` can optionally be specified, to ensure these fields have
        the correct value in the returned list. Otherwise, the first `main_script` and `script_variant` values
        found (for the given family) are used.
        '''
        family_names = family_name_or_names
        if isinstance(family_names, str):
            family_names = [family_names]
        font_infos = self.known_fonts(lambda font_info: font_info.family_name in family_names)
        if len(font_infos) == 0:
            return font_infos
        # font_infos can be duplicated under multiple script variants. If no script and variant is specified, we
        # just pick the first.
        if main_script is None:
            main_script = font_infos[0].main_script
        if script_variant is None:
            script_variant = font_infos[0].script_variant
        font_infos = [font_info for font_info in font_infos if font_info.main_script == main_script and \
                                                               font_info.script_variant == script_variant]
        count_func = len
        font_infos = self._apply_pref_dict(main_script, script_variant, self.family_member_prefs, count_func,
                                           font_infos)
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

        # print("After each filter func")
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

    def all_installed_families(self) -> list[str]:
        '''Returns a list of strings of the family names of all fonts installed on the system.
        '''
        font_platform = _platforms.get_font_platform()
        return font_platform.all_installed_families()        

    def installed_families(self, family_name_or_names) -> list[str]:
        family_names = family_name_or_names
        if isinstance(family_names, str):
            family_names = [family_names]
        all_installed_families = set(self.all_installed_families())
        return [family_name for family_name in family_names if family_name in all_installed_families]

    def not_installed_families(self, family_name_or_names) -> list[str]:
        family_names = family_name_or_names
        if isinstance(family_names, str):
            family_names = [family_names]
        all_installed_families = set(self.all_installed_families())
        return [family_name for family_name in family_names if family_name not in all_installed_families]

    def download_fonts(self, font_infos, download_dir = None) -> tempfile.TemporaryDirectory | None:
        temp_dir = None
        if download_dir is None:
            temp_dir = tempfile.TemporaryDirectory()
            download_dir = Path(temp_dir.name)
        else:
            download_dir = Path(download_dir)
        font_infos = [font_info.copy() for font_info in font_infos]
        for font_info in font_infos:
            if font_info.url is None or font_info.url == "":
                continue
            response = requests.get(font_info.url, stream=True)
            font_info.path = download_dir / font_info.filename
            with open(font_info.path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=128):
                    file.write(chunk)
        return temp_dir

    def install_fonts(self, font_infos) -> None:
        font_platform = _platforms.get_font_platform()
        font_platform.install_fonts(font_infos)        
     
    def uninstall_fonts(self, font_infos) -> None:
        font_platform = _platforms.get_font_platform()
        font_platform.uninstall_fonts(font_infos)        

    def known_fonts(self, filter_func = None) -> list[FontInfo]:
        '''Returns a list of FontInfo objects for all fonts known to this library.
        
        This is a large list, which is cached in memory the first time the method is called.'''
        # Even though noto.get_noto_fonts() can filter on the fly, for now we choose to optimise for speed, rather
        # than memory, by caching the full list of font_infos in memory.
        if self._all_known_fonts is None:
            self._all_known_fonts = noto.get_noto_fonts()
        return [font_info for font_info in self._all_known_fonts if (filter_func is None or filter_func(font_info))]

    def known_scripts(self, filter_func = None) -> list[str]:
        '''Returns a list of the `main_script` values for all the fonts known to this library.'''
        return sorted(set([info.main_script for info in self.known_fonts(filter_func)]))

    def known_script_variants(self, filter_func = None) -> list[(str, str)]:
        '''Returns a list of `(main_script, script_variant)` tuples for all the fonts known to this library.'''
        # Use a dictionary as an ordered set
        return list({(info.main_script, info.script_variant): 1 for info in self.known_fonts(filter_func)}.keys())

    def all_unicode_scripts(self) -> list[str]:
        '''Returns a list of all script values in the Unicode standard.'''
        return list(udp.property_value_aliases['script'].keys())

    def scripts_not_known(self) -> list[str]:
        '''Returns a list of all the Unicode script values not supported by the fonts known to this library.'''
        return sorted(set(self.all_unicode_scripts()) - set(self.known_scripts()) -
                      set(["Common", "Inherited", "Unknown"]))

    @property
    def _small_unihan_data(self):
        if self._small_unihan_data_private is None:
            with open(_SMALL_UNIHAN_PATH) as small_unihan_file:
                self._small_unihan_data_private = json.load(small_unihan_file)
        return self._small_unihan_data_private


ANY_SCRIPT = object()
'''Sentinel for preference matching on any script.'''


class FontFinderException(Exception):
    '''Base Exception class for this library.'''
    pass


class UnsupportedPlatformException(FontFinderException):
    '''Raised when an operation is not supported on the current operating system.'''
    pass

