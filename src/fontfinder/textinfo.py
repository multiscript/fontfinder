from collections import Counter
from dataclasses import dataclass, field


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