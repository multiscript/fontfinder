import copy

from fontfinder.fontinfo import FontInfo, FontForm, FontWidth, FontWeight, FontStyle, FontFormat, FontBuild 

cjk_base_url = "https://github.com/notofonts/noto-cjk/blob/main/"

cjk_weights =   [
    ("Black",       FontWeight.BLACK),
    ("Bold",        FontWeight.BOLD),
    ("DemiLight",   FontWeight.DEMI_LIGHT),
    ("Light",       FontWeight.LIGHT),
    ("Medium",      FontWeight.MEDIUM),
    ("Regular",     FontWeight.REGULAR),
    ("Thin",        FontWeight.THIN),                
]

SCRIPT_INFO_KEY = "script_info"
URL_COMPONENT_KEY = "url_component"
CJK_CODE_KEY = "cjk_code"

cjk_data = {
    "chinese-simplified":
        {
            SCRIPT_INFO_KEY: [
                ("Han", "zh-Hans")
            ],
            URL_COMPONENT_KEY:    "SimplifiedChinese/",
            CJK_CODE_KEY:         "SC",
        },
    "chinese-traditional":
        {
            SCRIPT_INFO_KEY: [
                ("Han", "zh-Hant"), ("Bopomofo", ""),
            ],
            URL_COMPONENT_KEY:    "TraditionalChinese/",
            CJK_CODE_KEY:         "TC",
        },
    "chinese-hongkong":
        {
            SCRIPT_INFO_KEY: [
                ("Han", "zh-Hant-HK")
            ],
            URL_COMPONENT_KEY:    "TraditionalChineseHK/",
            CJK_CODE_KEY:         "HK",
        },
    "japanese":
        {
            SCRIPT_INFO_KEY: [
                ("Hiragana", ""), ("Katakana", ""), ("Han", "ja")
            ],
            URL_COMPONENT_KEY:    "Japanese/",
            CJK_CODE_KEY:         "JP",
        },
    "korean":
        {
            SCRIPT_INFO_KEY: [
                ("Hangul", ""), ("Han", "ko")
            ],
            URL_COMPONENT_KEY:    "Korean/",
            CJK_CODE_KEY:         "KR",
        },
}


def get_noto_cjk_fonts():
    cjk_fonts = []
    for lang, lang_data in cjk_data.items():
        cjk_code = lang_data[CJK_CODE_KEY]
        url_component = lang_data[URL_COMPONENT_KEY]
        script_infos = lang_data[SCRIPT_INFO_KEY]
        for form in [FontForm.SANS_SERIF, FontForm.SERIF]:
            form_name = "Sans" if form is FontForm.SANS_SERIF else "Serif"
            lang_fonts = []
            for weight_name, weight in cjk_weights:
                family_name = f"Noto {form_name} CJK {cjk_code.upper()}"
                postscript_name = f"Noto{form_name}CJK{cjk_code.lower()}-{weight_name}"
                url = f"{cjk_base_url}{form_name}/OTF/{url_component}{postscript_name}.otf"
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
                    cjk_fonts.append(font_info)

    return cjk_fonts
