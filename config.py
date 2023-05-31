import os
from pathlib import Path
from dotenv import load_dotenv

root_dir = os.path.dirname(Path(__file__))


def normalize_path(path):
    sep = os.sep
    desep = "/"
    if sep == "/":
        desep = "\\"
    return path.replace(desep, sep)


load_dotenv()

LOGGING_DIR = normalize_path(os.getenv('LOGGING'))
TABLE_PARTS_DIR = normalize_path(os.getenv('TABLE_PARTS'))
CATEGORIES_JSON = normalize_path(os.getenv('CATEGORIES_JSON'))

# FONTS
ARIALN = normalize_path(os.getenv('ARIALN'))
