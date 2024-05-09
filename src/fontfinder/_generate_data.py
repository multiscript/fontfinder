
import json
from pathlib import Path
import tempfile

import fontfinder


def generate_small_unihan():
    '''Utility function for creating a subset of the Unicode Unihan database needed by `fontfinder`.
    This function recreates the local subset. As `fontfinder` is distributed with a working reference
    copy of the subset (`small_unihan.json`) you should never need to call this method.'''
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
            with open(fontfinder._SMALL_UNIHAN_PATH, "w") as small_unihan_file:
                full_records = json.load(full_unihan_file)
                selected_keys = ['kTraditionalVariant', 'kSimplifiedVariant']
                small_records = {}
                for full_record in full_records:
                    small_entry = {key: value for key, value in full_record.items() if key in selected_keys}
                    if len(small_entry) > 0:
                        small_records[full_record['char']] = small_entry
                json.dump(small_records, small_unihan_file)
        

if __name__ == '__main__':
    generate_small_unihan()

