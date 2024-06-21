
'''
Utility script for downloading and generating local copies of Unicode and Noto data for use by fontfinder.
This script is only used during development, and not by users of fontfinder.
'''
import json
from pathlib import Path
import tempfile

import requests

import fontfinder
from fontfinder import noto


def download_noto_ref_data():
    response = requests.get(noto.NOTO_MAIN_JSON_URL)
    with open(noto._NOTO_MAIN_JSON_REF_PATH, "w", encoding="utf-8") as file:
        file.write(response.text)

def download_script_metadata_ref():
    response = requests.get(fontfinder._SCRIPT_METADATA_URL)
    with open(fontfinder._SCRIPT_METADATA_PATH, "w", encoding="utf-8") as file:
        file.write(response.text)

def generate_small_unihan():
    '''Creates the subset of the Unicode Unihan database needed by `fontfinder`.'''
    import unihan_etl.core

    with tempfile.TemporaryDirectory() as full_unihan_dir:
        full_unihan_path = Path(full_unihan_dir, "full_unihan.json").resolve()

        with tempfile.TemporaryDirectory() as work_dir:
            packager_options = {
                "destination": str(full_unihan_path),
                "work_dir": work_dir,
                "format": "json"
            }
            packager = unihan_etl.core.Packager(packager_options)
            packager.download()
            packager.export()

        with open(full_unihan_path) as full_unihan_file:
            with open(fontfinder._SMALL_UNIHAN_PATH, "w", encoding="utf-8") as small_unihan_file:
                full_records = json.load(full_unihan_file)
                selected_keys = ['kTraditionalVariant', 'kSimplifiedVariant']
                small_records = {}
                for full_record in full_records:
                    small_entry = {key: value for key, value in full_record.items() if key in selected_keys}
                    if len(small_entry) > 0:
                        small_records[full_record['char']] = small_entry
                json.dump(small_records, small_unihan_file)
                print(f"Save small Unihan data to {fontfinder._SMALL_UNIHAN_PATH}")
        

if __name__ == '__main__':
    download_noto_ref_data()
    download_script_metadata_ref()
    generate_small_unihan()

