
import json
from pathlib import Path
import tempfile

import unihan_etl.process

import fontfinder

_FULL_UNIHAN_PATH = Path(fontfinder._DATA_DIR_PATH, "full_unihan.json").resolve()


def generate_small_unihan():
    with tempfile.TemporaryDirectory() as work_dir:
        packager_options = {
            "destination": str(_FULL_UNIHAN_PATH),
            "work_dir": work_dir,
            "format": "json"
        }
        packager = unihan_etl.process.Packager(packager_options)
        packager.download()
        packager.export()

    with open(_FULL_UNIHAN_PATH) as full_unihan_file:
        with open(fontfinder._SMALL_UNIHAN_PATH, "w") as small_unihan_file:
            full_records = json.load(full_unihan_file)
            selected_keys = ['kTraditionalVariant', 'kSimplifiedVariant']
            small_records = {}
            for full_record in full_records:
                small_entry = {key: value for key, value in full_record.items() if key in selected_keys}
                if len(small_entry) > 0:
                    small_records[full_record['char']] = small_entry
            json.dump(small_records, small_unihan_file)
    
    _FULL_UNIHAN_PATH.unlink()


if __name__ == '__main__':
    generate_small_unihan()

