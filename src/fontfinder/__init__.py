from collections import Counter
import dataclasses
import json
from pathlib import Path

import requests
import unicodedataplus as udp


DATA_DIR_PATH = Path(__file__, "../data").resolve()
DATA_DIR_PATH.mkdir(parents=True, exist_ok=True)
SMALL_UNIHAN_PATH = Path(DATA_DIR_PATH, "small_unihan.json").resolve()
MAX_CHARS_TO_ANALYSE = 2048


class FontFinder:
    def __init__(self):
        self.load_data()

    def load_data(self):
        self.noto_data = requests.get("https://notofonts.github.io/noto.json").json()
        
        with open(SMALL_UNIHAN_PATH) as small_unihan_file:
            self.small_unihan_data = json.load(small_unihan_file)
    
    def get_text_info(self, text):
        script_counter = Counter()
        unihan_counter = Counter()
        ignore_scripts = set(['Common', 'Inherited', 'Unknown'])
        for char in text[0:min(len(text), MAX_CHARS_TO_ANALYSE)]:
            script = udp.script(char)
            if script not in ignore_scripts:
                script_counter[script] += 1
            if char in self.small_unihan_data:
                for key in self.small_unihan_data[char].keys():
                    unihan_counter[key] += 1

        main_script = script_counter.most_common(1)[0][0]

        if main_script == 'Han':
            # Han script can be used by Chinese, Japanese and Korean texts
            if 'Hangul' in script_counter:
                # If Hangul characters are present, assume it's Korean
                main_script = 'Korean'
            elif 'Hiragana' in script_counter or 'Katakana' in script_counter:
                # If Hirogana or Katakana characters are present, assume it's Japanese
                main_script = 'Japanese'
            elif unihan_counter['kSimplifiedVariant'] > unihan_counter['kTraditionalVariant']:
                # Traditional Chinese characters have simplified variants, and vice versa.
                # So if there are more simplified variants than traditional, we likely have traditional text,
                # and vice-versa.
                main_script = 'Chinese (Traditional)'
            else:
                main_script = 'Chinese (Simplified)'
        elif main_script == 'Hangul':
            main_script = 'Korean'
        elif main_script in ['Hiragana', 'Katakana']:
            main_script = 'Japanese'

        text_info = TextInfo(main_script=main_script, script_order=script_counter.most_common())
        return text_info


@dataclasses.dataclass
class TextInfo:
    main_script: str
    script_order: list[tuple[str, int]]
