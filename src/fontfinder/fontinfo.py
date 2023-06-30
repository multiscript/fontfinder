from dataclasses import dataclass
import re
from enum import Enum, auto


@dataclass
class FontFileInfo:
    script: str
    '''Primary Unicode script covered by the font.'''

    family: str
    '''Font family name.'''

    form: 'FontForm'

    build: 'FontBuild'

    width: 'FontWidth'
    
    weight: 'FontWeight'

    style: 'FontStyle'

    format: 'FontFormat'

    postscript_name: str

    url: str = None
    '''URL download source for the font.'''

    def __init__(self, script: str = None, family: str = None, form: 'FontForm' = None, build: 'FontBuild' = None,
                 width: 'FontWidth' = None, weight: 'FontWeight' = None, style: 'FontStyle' = None,
                 format: 'FontFormat' = None, postscript_name: str = None, url: str  = None,
                 *, from_str: str = None):

        if from_str is not None:
            self.form = FontForm.from_str(from_str) if form is None else form
            self.build = FontBuild.from_str(from_str) if build is None else build
            self.width = FontWidth.from_str(from_str) if width is None else width
            self.weight = FontWeight.from_str(from_str) if weight is None else weight
            self.style = FontStyle.from_str(from_str) if style is None else style
            self.format = FontFormat.from_str(from_str) if format is None else format
        else:
            self.form = FontForm.UNSET if form is None else form
            self.build = FontBuild.UNSET if build is None else build
            self.width = FontWidth.NORMAL if width is None else width
            self.weight = FontWeight.REGULAR if weight is None else weight
            self.style = FontStyle.UPRIGHT if style is None else style
            self.format = FontFormat.UNSET if format is None else format

        self.script = "" if script is None else script
        self.family = "" if family is None else family
        self.postscript_name = "" if postscript_name is None else postscript_name
        self.url = "" if url is None else url





class FontForm(Enum):
    UNSET       = auto()
    SERIF       = auto()
    SANS_SERIF  = auto()

    @classmethod
    def from_str(cls, string: str):
        result = FontForm.UNSET
        for font_form, regex in font_form_regexes.items():
            if regex.search(string):
                result = font_form
        return result


font_form_regexes = {
    FontForm.SERIF:         re.compile(r"Serif",    re.IGNORECASE),
    FontForm.SANS_SERIF:    re.compile(r"Sans",     re.IGNORECASE)
}


class FontBuild(Enum):
    UNSET       = auto()
    UNHINTED    = auto()
    HINTED      = auto()
    FULL        = auto()

    @classmethod
    def from_str(cls, string: str):
        result = FontBuild.UNSET
        for font_build, regex in font_build_regexes.items():
            if regex.search(string):
                result = font_build
        return result

font_build_regexes = {
    FontBuild.HINTED:      re.compile(r"Hinted",    re.IGNORECASE),
    FontBuild.UNHINTED:    re.compile(r"Unhinted",  re.IGNORECASE),
    FontBuild.FULL:        re.compile(r"Full",      re.IGNORECASE)
}


class FontWidth(Enum):
    NORMAL      = auto()
    VAR_WIDTH   = auto()
    EXTRA_COND  = auto()
    CONDENSED   = auto()
    SEMI_COND   = auto()

    @classmethod
    def from_str(cls, string: str):
        result = FontWidth.NORMAL
        for font_width, regex in font_width_regexes.items():
            if regex.search(string):
                result = font_width
        return result


font_width_regexes = {
    FontWidth.VAR_WIDTH:    re.compile(r"wdth",             re.IGNORECASE),
    FontWidth.CONDENSED:    re.compile(r"Condensed",        re.IGNORECASE),
    FontWidth.EXTRA_COND:   re.compile(r"Extra.?Condensed", re.IGNORECASE),
    FontWidth.SEMI_COND:    re.compile(r"Semi.?Condensed",  re.IGNORECASE),
}


class FontWeight(Enum):
    REGULAR     = auto()
    VAR_WEIGHT  = auto()
    EXTRA_LIGHT = auto()
    LIGHT       = auto()
    THIN        = auto()
    MEDIUM      = auto()
    SEMI_BOLD   = auto()
    BOLD        = auto()
    EXTRA_BOLD  = auto()
    BLACK       = auto()

    @classmethod
    def from_str(cls, string: str):
        result = FontWeight.REGULAR
        for font_width, regex in font_weight_regexes.items():
            if regex.search(string):
                result = font_width
        return result


font_weight_regexes = {
    FontWeight.VAR_WEIGHT:      re.compile(r"wght",             re.IGNORECASE),
    FontWeight.LIGHT:           re.compile(r"Light",            re.IGNORECASE),
    FontWeight.EXTRA_LIGHT:     re.compile(r"Extra.?Light",     re.IGNORECASE),
    FontWeight.THIN:            re.compile(r"Thin",             re.IGNORECASE),
    FontWeight.MEDIUM:          re.compile(r"Medium",           re.IGNORECASE),
    FontWeight.BOLD:            re.compile(r"Bold",             re.IGNORECASE),
    FontWeight.SEMI_BOLD:       re.compile(r"Semi.?Bold",       re.IGNORECASE),
    FontWeight.EXTRA_BOLD:      re.compile(r"Extra.?Bold",      re.IGNORECASE),
    FontWeight.BLACK:           re.compile(r"Black",            re.IGNORECASE),
}


class FontStyle(Enum):
    UPRIGHT     = auto()
    ITALIC      = auto()
 
    @classmethod
    def from_str(cls, string: str):
        result = FontStyle.UPRIGHT
        for font_style, regex in font_style_regexes.items():
            if regex.search(string):
                result = font_style
        return result


font_style_regexes = {
    FontStyle.ITALIC:          re.compile(r"Italic",            re.IGNORECASE),
}


class FontFormat(Enum):
    UNSET       = ""
    OTF         = "OTF"
    OTC         = "OTC"
    TTF         = "TTF"

    @classmethod
    def from_str(cls, string: str):
        result = FontFormat.UNSET
        for font_format, regex in font_format_regexes.items():
            if regex.search(string):
                result = font_format
        return result


font_format_regexes = {
    FontFormat.OTF:             re.compile(r"\.OTF",            re.IGNORECASE),
    FontFormat.OTC:             re.compile(r"\.OTC",            re.IGNORECASE),
    FontFormat.TTF:             re.compile(r"\.TTF",            re.IGNORECASE),
}
