
from fontfinder import FontFinder
import unicodedataplus as udp
from pprint import pprint

sample_text = ''''
'''


class TestFontFinder:

    def test_initial_devel(self):
        ff = FontFinder()
        pprint(ff.count_scripts(sample_text))
