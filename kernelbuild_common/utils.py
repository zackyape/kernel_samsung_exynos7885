from pathlib import Path
import zipfile
import re

from .loginit import logging


def check_file(filename: Path):
    log = f"Check {filename}... "
    exist = filename.exists()
    if not exist:
        log += "Not found"
    else:
        log += "Found"
    logging.info(log)
    return exist


def print_dictinfo(info: "dict[str, str]"):
    logging.info("=" * 32)
    for k, v in info.items():
        logging.info(f"{k}={v}")
    logging.info("=" * 32)


def zip_files(zipfilename: str, files: "list[str]"):
    logging.info(f"Zipping {len(files)} files to {zipfilename}...")
    with zipfile.ZipFile(zipfilename, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for f in files:
            zf.write(f)
    logging.info("OK")


def match_and_get(regex: str, pattern: str) -> str:
    matched = re.search(regex, pattern)
    if not matched:
        raise AssertionError(f"Failed to match: for pattern: {pattern} regex: {regex}")
    return matched.group(1)
