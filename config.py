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

LOGGING_DIR = os.path.join(root_dir, normalize_path(os.getenv('LOGGING')))
TABLE_PARTS_DIR = os.path.join(root_dir, normalize_path(os.getenv('TABLE_PARTS')))
CATEGORIES_JSON = os.path.join(root_dir, normalize_path(os.getenv('CATEGORIES_JSON')))

# PNG
ARROW_PNG = os.path.join(root_dir, normalize_path(os.getenv('ARROW_PNG')))

# FONTS
ARIALN = normalize_path(os.getenv('ARIALN'))
