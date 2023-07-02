from dataclasses import dataclass
import re
from enum import Enum, auto


@dataclass
class FontFileInfo:
    script_name: str
    '''Primary Unicode script covered by the font.'''

    family_name: str
    '''Font family name'''

    style_name: str
    '''Font style name'''

    postscript_name: str
    '''Font PostScript name'''

    url: str
    '''URL download source for the font.'''

    form: 'FontForm'

    width: 'FontWidth'
    
    weight: 'FontWeight'

    style: 'FontStyle'

    format: 'FontFormat'

    build: 'FontBuild'

    def __init__(self, script_name: str = None, family_name: str = None, style_name: str = None,
                 postscript_name: str = None, url: str  = None, form: 'FontForm' = None, 
                 width: 'FontWidth' = None, weight: 'FontWeight' = None, style: 'FontStyle' = None,
                 format: 'FontFormat' = None, build: 'FontBuild' = None,
                 *, from_str: str = None):

        if from_str is not None:
            self.form = FontForm.from_str(from_str) if form is None else form
            self.width = FontWidth.from_str(from_str) if width is None else width
            self.weight = FontWeight.from_str(from_str) if weight is None else weight
            self.style = FontStyle.from_str(from_str) if style is None else style
            self.format = FontFormat.from_str(from_str) if format is None else format
            self.build = FontBuild.from_str(from_str) if build is None else build
        else:
            self.form = FontForm.UNSET if form is None else form
            self.width = FontWidth.NORMAL if width is None else width
            self.weight = FontWeight.REGULAR if weight is None else weight
            self.style = FontStyle.UPRIGHT if style is None else style
            self.format = FontFormat.UNSET if format is None else format
            self.build = FontBuild.UNSET if build is None else build

        self.script_name = "" if script_name is None else script_name
        self.family_name = "" if family_name is None else family_name
        self.style_name = "" if style_name is None else style_name
        self.postscript_name = "" if postscript_name is None else postscript_name
        self.url = "" if url is None else url


class FontForm(Enum):
    UNSET       = auto()
    SERIF       = auto()
    SANS_SERIF  = auto()

    @property
    def text(self):
        return font_form_data[self][0]

    @classmethod
    def from_str(cls, string: str):
        result = FontForm.UNSET
        for font_form, data in font_form_data.items():
            if data[1].search(string):
                result = font_form
        return result


font_form_data = {
    FontForm.SERIF:         ("Serif", re.compile(r"Serif",    re.IGNORECASE)),
    FontForm.SANS_SERIF:    ("Sans",  re.compile(r"Sans",     re.IGNORECASE))
}


class FontWidth(Enum):
    NORMAL      = auto()
    VARIABLE    = auto()
    EXTRA_COND  = auto()
    CONDENSED   = auto()
    SEMI_COND   = auto()

    @property
    def text(self):
        return font_width_data[self][0]

    @classmethod
    def from_str(cls, string: str):
        result = FontWidth.NORMAL
        for font_width, data in font_width_data.items():
            if data[1].search(string):
                result = font_width
        return result


font_width_data = {
    FontWidth.VARIABLE:    ("wdth",           re.compile(r"wdth",             re.IGNORECASE)),
    FontWidth.CONDENSED:    ("Condensed",      re.compile(r"Condensed",        re.IGNORECASE)),
    FontWidth.EXTRA_COND:   ("ExtraCondensed", re.compile(r"Extra.?Condensed", re.IGNORECASE)),
    FontWidth.SEMI_COND:    ("SemiCondensed",  re.compile(r"Semi.?Condensed",  re.IGNORECASE)),
}


class FontWeight(Enum):
    REGULAR     = auto()
    VARIABLE    = auto()
    EXTRA_LIGHT = auto()
    LIGHT       = auto()
    THIN        = auto()
    MEDIUM      = auto()
    SEMI_BOLD   = auto()
    BOLD        = auto()
    EXTRA_BOLD  = auto()
    BLACK       = auto()

    @property
    def text(self):
        return font_weight_data[self][0]

    @classmethod
    def from_str(cls, string: str):
        result = FontWeight.REGULAR
        for font_width, data in font_weight_data.items():
            if data[1].search(string):
                result = font_width
        return result


font_weight_data = {
    FontWeight.VARIABLE:      ("wght",       re.compile(r"wght",             re.IGNORECASE)),
    FontWeight.LIGHT:           ("Light",      re.compile(r"Light",            re.IGNORECASE)),
    FontWeight.EXTRA_LIGHT:     ("ExtraLight", re.compile(r"Extra.?Light",     re.IGNORECASE)),
    FontWeight.THIN:            ("Thin",       re.compile(r"Thin",             re.IGNORECASE)),
    FontWeight.MEDIUM:          ("Medium",     re.compile(r"Medium",           re.IGNORECASE)),
    FontWeight.BOLD:            ("Bold",       re.compile(r"Bold",             re.IGNORECASE)),
    FontWeight.SEMI_BOLD:       ("SemiBold",   re.compile(r"Semi.?Bold",       re.IGNORECASE)),
    FontWeight.EXTRA_BOLD:      ("ExtraBold",  re.compile(r"Extra.?Bold",      re.IGNORECASE)),
    FontWeight.BLACK:           ("Black",      re.compile(r"Black",            re.IGNORECASE)),
}


class FontStyle(Enum):
    UPRIGHT     = auto()
    ITALIC      = auto()
 
    @property
    def text(self):
        return font_style_data[self][0]

    @classmethod
    def from_str(cls, string: str):
        result = FontStyle.UPRIGHT
        for font_style, data in font_style_data.items():
            if data[1].search(string):
                result = font_style
        return result


font_style_data = {
    FontStyle.ITALIC:          ("Italic", re.compile(r"Italic",            re.IGNORECASE)),
}


class FontFormat(Enum):
    UNSET       = ""
    OTF         = "OTF"
    OTC         = "OTC"
    TTF         = "TTF"

    @property
    def text(self):
        return font_format_data[self][0]

    @classmethod
    def from_str(cls, string: str):
        result = FontFormat.UNSET
        for font_format, data in font_format_data.items():
            if data[1].search(string):
                result = font_format
        return result


font_format_data = {
    FontFormat.OTF:             ("OTF", re.compile(r"\.OTF",            re.IGNORECASE)),
    FontFormat.OTC:             ("OTC", re.compile(r"\.OTC",            re.IGNORECASE)),
    FontFormat.TTF:             ("TTF", re.compile(r"\.TTF",            re.IGNORECASE)),
}


class FontBuild(Enum):
    UNSET       = auto()
    UNHINTED    = auto()
    HINTED      = auto()
    FULL        = auto()

    @property
    def text(self):
        return font_build_data[self][0]

    @classmethod
    def from_str(cls, string: str):
        result = FontBuild.UNSET
        for font_build, data in font_build_data.items():
            if data[1].search(string):
                result = font_build
        return result


font_build_data = {
    FontBuild.HINTED:      ("Hinted",   re.compile(r"Hinted",    re.IGNORECASE)),
    FontBuild.UNHINTED:    ("Unhinted", re.compile(r"Unhinted",  re.IGNORECASE)),
    FontBuild.FULL:        ("Full",     re.compile(r"Full",      re.IGNORECASE))
}
