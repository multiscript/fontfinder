import copy
import datetime
from pathlib import Path
import requests
import shutil

import fontfinder
from fontfinder.fontinfo import FontInfo, FontForm, FontWidth, FontWeight, FontStyle, FontFormat, FontBuild 

NOTO_MAIN_JSON_URL = "https://notofonts.github.io/noto.json"
NOTO_MAIN_BASE_URL = "https://cdn.jsdelivr.net/gh/notofonts/notofonts.github.io/"
NOTO_CJK_BASE_URL = "https://github.com/notofonts/noto-cjk/raw/main/"

_NOTO_MAIN_JSON_PATH = Path(fontfinder._DATA_DIR_PATH, "noto_main.json").resolve()
_NOTO_MAIN_JSON_UPDATE_DELTA = datetime.timedelta(days=1)

def get_noto_fonts():
    '''Return a list of FontInfo records for the Google Noto fonts.'''
    font_infos = _get_noto_main_fonts()
    font_infos.extend(_get_noto_cjk_fonts())
    font_infos.sort()
    return font_infos

def _get_noto_main_json_data():
    update_local_copy = False
    if _NOTO_MAIN_JSON_PATH.exists():
        last_mod_time = datetime.fromtimestampe(_NOTO_MAIN_JSON_PATH.stat().st_mtime)
        if (datetime.datetime.now() - last_mod_time) >= _NOTO_MAIN_JSON_UPDATE_DELTA:
            update_local_copy = True
    else:
        update_local_copy = True
    
    if update_local_copy:
        pass
    else:
        pass
        # Read local copy
            
def _get_noto_main_fonts():
    '''Return a list of FontInfo records for the main (non-CJK) Google Noto fonts.'''
    font_infos = []
    noto_data = requests.get(NOTO_MAIN_JSON_URL).json()
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
                        url = NOTO_MAIN_BASE_URL + relative_url
                        font_info = FontInfo(main_script=main_script, family_name=family_name, url=url)
                        font_info.set_from_noto_url(url)
                        # Form and build have already been set from the URL, but we can ensure the values are
                        # correct from the other JSON data.
                        font_info.form = form
                        font_info.build = build
                        font_infos.append(font_info)
    return font_infos


_CJK_WEIGHTS =   [
    ("Black",       FontWeight.BLACK),
    ("Bold",        FontWeight.BOLD),
    ("DemiLight",   FontWeight.DEMI_LIGHT),
    ("Light",       FontWeight.LIGHT),
    ("Medium",      FontWeight.MEDIUM),
    ("Regular",     FontWeight.REGULAR),
    ("Thin",        FontWeight.THIN),                
]

_CJK_SCRIPT_INFO_KEY = "script_info"
_CJK_URL_COMPONENT_KEY = "url_component"
_CJK_CODE_KEY = "cjk_code"

_CJK_DATA = {
    "chinese-simplified": {
            _CJK_SCRIPT_INFO_KEY:   [("Han", "zh-Hans")],
            _CJK_URL_COMPONENT_KEY: "SimplifiedChinese/",
            _CJK_CODE_KEY:          "SC"
        },
    "chinese-traditional": {
            _CJK_SCRIPT_INFO_KEY:   [("Han", "zh-Hant"), ("Bopomofo", "")],
            _CJK_URL_COMPONENT_KEY: "TraditionalChinese/",
            _CJK_CODE_KEY:          "TC",
        },
    "chinese-hongkong": {
            _CJK_SCRIPT_INFO_KEY:   [("Han", "zh-Hant-HK")],
            _CJK_URL_COMPONENT_KEY: "TraditionalChineseHK/",
            _CJK_CODE_KEY:          "HK",
        },
    "japanese": {
            _CJK_SCRIPT_INFO_KEY:   [("Hiragana", ""), ("Katakana", ""), ("Han", "ja")],
            _CJK_URL_COMPONENT_KEY: "Japanese/",
            _CJK_CODE_KEY:          "JP",
        },
    "korean": {
            _CJK_SCRIPT_INFO_KEY:   [("Hangul", ""), ("Han", "ko")],
            _CJK_URL_COMPONENT_KEY: "Korean/",
            _CJK_CODE_KEY:          "KR",
        },
}


def _get_noto_cjk_fonts():
    '''Return a list of FontInfo records for the CJK Google Noto fonts.'''
    font_infos = []
    for lang, lang_data in _CJK_DATA.items():
        cjk_code = lang_data[_CJK_CODE_KEY]
        url_component = lang_data[_CJK_URL_COMPONENT_KEY]
        script_infos = lang_data[_CJK_SCRIPT_INFO_KEY]
        for form in [FontForm.SANS_SERIF, FontForm.SERIF]:
            form_name = "Sans" if form is FontForm.SANS_SERIF else "Serif"
            lang_fonts = []
            for weight_name, weight in _CJK_WEIGHTS:
                # We're using the language-specific OTF versions of the Noto CJK fonts.
                family_name = f"Noto {form_name} CJK {cjk_code.upper()}"
                postscript_name = f"Noto{form_name}CJK{cjk_code.lower()}-{weight_name}"
                url = f"{NOTO_CJK_BASE_URL}{form_name}/OTF/{url_component}{postscript_name}.otf"
                lang_fonts.append(
                    FontInfo(main_script="", script_variant="", family_name=family_name, subfamily_name=weight_name,
                            postscript_name=postscript_name, form=form, width=FontWidth.NORMAL,
                            weight=weight, style=FontStyle.UPRIGHT, format=FontFormat.OTF,
                            build=FontBuild.FULL, url=url
                            )                
                )
            
            for main_script, script_variant in script_infos:
                for font_info in lang_fonts:
                    font_info = copy.copy(font_info)
                    font_info.main_script = main_script
                    font_info.script_variant = script_variant
                    font_infos.append(font_info)
    return font_infos
