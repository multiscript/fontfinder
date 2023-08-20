import csv
import dataclasses
from enum import Enum, Flag, auto
from pathlib import PurePosixPath
import re
from urllib.parse import urlparse


@dataclasses.dataclass
class FontInfo:
    script_name: str
    '''Primary Unicode script covered by the font.'''

    script_variant: str
    '''Script variant covered by the font.'''

    family_name: str
    '''Font family name'''

    subfamily_name: str
    '''Font subfamily name (also referred to as the style name)'''

    postscript_name: str
    '''Font PostScript name'''

    form: 'FontForm'

    width: 'FontWidth'
    
    weight: 'FontWeight'

    style: 'FontStyle'

    format: 'FontFormat'

    build: 'FontBuild'

    tags: 'FontTag'

    url: str
    '''URL download source for the font.'''

    def __init__(self, script_name: str = None, script_variant: str = None, family_name: str = None,
                 subfamily_name: str = None, postscript_name: str = None, form: 'FontForm' = None,
                 width: 'FontWidth' = None, weight: 'FontWeight' = None, style: 'FontStyle' = None,
                 format: 'FontFormat' = None, build: 'FontBuild' = None, tags: 'FontTag' = None, url: str  = None, 
                ):

        self.script_name = "" if script_name is None else script_name
        self.script_variant = "" if script_variant is None else script_variant
        self.family_name = "" if family_name is None else family_name
        self.subfamily_name = "" if subfamily_name is None else subfamily_name
        self.postscript_name = "" if postscript_name is None else postscript_name
        self.form = FontForm.UNSET if form is None else form
        self.width = FontWidth.NORMAL if width is None else width
        self.weight = FontWeight.REGULAR if weight is None else weight
        self.style = FontStyle.UPRIGHT if style is None else style
        self.format = FontFormat.UNSET if format is None else format
        self.build = FontBuild.UNSET if build is None else build
        self.tags = FontTag(0) if tags is None else tags
        self.url = "" if url is None else url

    def set_from_noto_url(self, url):
        url_path = urlparse(url).path
        self.form = FontForm.from_str(url_path)
        self.width = FontWidth.from_str(url_path)
        self.weight = FontWeight.from_str(url_path)
        self.style = FontStyle.from_str(url_path)
        self.format = FontFormat.from_str(url_path)
        self.build = FontBuild.from_str(url_path)
        
        stem = PurePosixPath(url_path).stem
        self.postscript_name = re.sub(r"\[.*\]", "", stem)
        self.subfamily_name = self.postscript_name.split('-')[-1]

        if self.width is FontWidth.VARIABLE or self.weight is FontWeight.VARIABLE:
            self.subfamily_name = FontWeight.REGULAR.text
            self.postscript_name += "-" + FontWeight.REGULAR.text
        
        if "/slim".casefold() in url_path.casefold():
            self.tags |= FontTag.SLIM
        if "Mono".casefold() in self.postscript_name.casefold():
            self.tags |= FontTag.MONO
        if "UI" in self.postscript_name:
            self.tags |= FontTag.UI
        if "Display".casefold() in self.postscript_name.casefold():
            self.tags |= FontTag.DISPLAY
        if self.postscript_name.startswith("NotoSansNotoSansTifinagh"):
            pass
        match = re.match(r"NotoSansTifinagh(?P<variant>.*?)-", self.postscript_name)
        if match is not None:
            self.script_variant = match['variant']
        self.url = url

    def str_dict(self):
        str_dict = dataclasses.asdict(self)
        # Convert Enum-type fields to their string names without the Enum type-name
        for field_name, field_value in str_dict.items():
            if isinstance(field_value, Flag):
                name_list = []
                for member in type(field_value):
                    if member in field_value:
                        name_list.append(member.name)
                str_dict[field_name] = "|".join(name_list)
            elif isinstance(field_value, Enum):
                str_dict[field_name] = str(field_value.name)
        return str_dict
    
    @classmethod
    def from_str_dict(cls, str_dict):
        # Convert the string names of Enum-type fields to Enum instances
        # Use an empty (but initialized) instance to confirm actual field types. (This is because we've used forward
        # references for their type declaration, which results in their dataclasses.field type showing
        # as str, not Enum)
        blank_obj_dict = dataclasses.asdict(cls())
        for field_name, field_value in blank_obj_dict.items():
            if isinstance(field_value, Flag):
                new_value = type(field_value)(0)
                for member_name in str_dict[field_name].split("|"):
                    if len(member_name) > 0:
                        new_value |= type(field_value)[member_name]
                str_dict[field_name] = new_value
            elif isinstance(field_value, Enum):
                # Indexing an Enum with the string member name returns the member
                str_dict[field_name] = type(field_value)[str_dict[field_name]]
            elif isinstance(field_value, bool):
                str_dict[field_name] = (str_dict[field_name].upper() == "TRUE")
        return cls(**str_dict)


def write_font_infos_to_csv(font_infos, csv_path):
    with open(csv_path, "w") as file:
        field_names = [field.name for field in dataclasses.fields(FontInfo)]
        writer = csv.DictWriter(file, field_names)
        writer.writeheader()
        for font in font_infos:
            writer.writerow(font.str_dict())

def read_font_infos_from_csv(csv_path):
    font_infos = []
    with open(csv_path, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            font_infos.append(FontInfo.from_str_dict(row))
    return font_infos


class FontForm(Enum):
    UNSET       = auto()
    SERIF       = auto()
    SANS_SERIF  = auto()

    @property
    def text(self):
        return font_form_str_data[self][0]

    @classmethod
    def from_str(cls, string: str):
        result = FontForm.UNSET
        for font_form, data in font_form_str_data.items():
            if data[1].search(string):
                result = font_form
        return result


font_form_str_data = {
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
        return font_width_str_data[self][0]

    @classmethod
    def from_str(cls, string: str):
        result = FontWidth.NORMAL
        for font_width, data in font_width_str_data.items():
            if data[1].search(string):
                result = font_width
        return result


font_width_str_data = {
    FontWidth.VARIABLE:     ("wdth",           re.compile(r"wdth",             re.IGNORECASE)),
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
        return font_weight_str_data[self][0]

    @classmethod
    def from_str(cls, string: str):
        result = FontWeight.REGULAR
        for font_width, data in font_weight_str_data.items():
            if data[1].search(string):
                result = font_width
        return result


font_weight_str_data = {
    FontWeight.VARIABLE:        ("wght",       re.compile(r"wght",             re.IGNORECASE)),
    FontWeight.REGULAR:         ("Regular",    re.compile(r"Regular",          re.IGNORECASE)),
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
        return font_style_str_data[self][0]

    @classmethod
    def from_str(cls, string: str):
        result = FontStyle.UPRIGHT
        for font_style, data in font_style_str_data.items():
            if data[1].search(string):
                result = font_style
        return result


font_style_str_data = {
    FontStyle.ITALIC:          ("Italic", re.compile(r"Italic",            re.IGNORECASE)),
}


class FontFormat(Enum):
    UNSET       = ""
    OTF         = "OTF"
    OTC         = "OTC"
    TTF         = "TTF"

    @property
    def text(self):
        return font_format_str_data[self][0]

    @classmethod
    def from_str(cls, string: str):
        result = FontFormat.UNSET
        for font_format, data in font_format_str_data.items():
            if data[1].search(string):
                result = font_format
        return result


font_format_str_data = {
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
        return font_build_str_data[self][0]

    @classmethod
    def from_str(cls, string: str):
        result = FontBuild.UNSET
        for font_build, data in font_build_str_data.items():
            if data[1].search(string):
                result = font_build
        return result


font_build_str_data = {
    FontBuild.HINTED:      ("Hinted",   re.compile(r"Hinted",    re.IGNORECASE)),
    FontBuild.UNHINTED:    ("Unhinted", re.compile(r"Unhinted",  re.IGNORECASE)),
    FontBuild.FULL:        ("Full",     re.compile(r"Full",      re.IGNORECASE))
}


class FontTag(Flag):
    MONO        = auto()
    UI          = auto() # UI font
    DISPLAY     = auto()
    SLIM        = auto() # Noto slim-build variable font
