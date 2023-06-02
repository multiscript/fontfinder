import json
from pathlib import Path
import requests
import unicodedataplus as udp
from pprint import pprint
from collections import Counter

DATA_DIR_PATH = Path(__file__, "../data").resolve()
DATA_DIR_PATH.mkdir(parents=True, exist_ok=True)
SMALL_UNIHAN_PATH = Path(DATA_DIR_PATH, "small_unihan.json").resolve()

class FontFinder:
    def __init__(self):
        self.load_data()

    def load_data(self):
        self.noto_data = requests.get("https://notofonts.github.io/noto.json").json()
        
        with open(SMALL_UNIHAN_PATH) as small_unihan_file:
            self.small_unihan_data = json.load(small_unihan_file)
    
    def count_scripts(self, text):
        script_count = Counter()
        unihan_count = Counter()
        ignore_scripts = set(['Common', 'Inherited', 'Unknown'])
        for char in text:
            script = udp.script(char)
            if script not in ignore_scripts:
                script_count[script] += 1
            if char in self.small_unihan_data:
                for key in self.small_unihan_data[char].keys():
                    unihan_count[key] += 1

        return script_count, unihan_count

