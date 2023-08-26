from fontfinder.fontinfo import ScriptInfo, FontWeight

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

cjk_data = {
    "chinese-simplified":
        {
            "script_infos": [
                ScriptInfo("Han", "zh-Hans")
            ],
            "url_component":    "Sans/OTF/SimplifiedChinese/",
            "cjk_suffix":       "sc",
            "url_suffix":       ".otf",
        },
    "chinese-traditional":
        {
            "script_infos": [
                ScriptInfo("Han", "zh-Hant"), ScriptInfo("Bopomofo"),
            ],
            "url_component":    "Sans/OTF/TraditionalChinese/",
            "cjk_suffix":       "tc",
            "url_suffix":       ".otf",
        },
    "chinese-hongkong":
        {
            "script_infos": [
                ScriptInfo("Han", "zh-Hant-HK")
            ],
            "url_component":    "Sans/OTF/TraditionalChineseHK/",
            "cjk_suffix":       "hk",
            "url_suffix":       ".otf",
        },
    "japanese":
        {
            "script_infos": [
                ScriptInfo("Hiragana"), ScriptInfo("Katakana"), ScriptInfo("Han", "ja")
            ],
            "url_component":    "Sans/OTF/Japanese/",
            "cjk_suffix":       "jp",
            "url_suffix":       ".otf",
        },
    "korean":
        {
            "script_infos": [
                ScriptInfo("Hangul" ), ScriptInfo("Han", "ko")
            ],
            "url_component":    "Sans/OTF/Korean/",
            "cjk_suffix":       "kr",
            "url_suffix":       ".otf",
        },
}