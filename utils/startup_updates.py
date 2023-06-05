# -*- coding: utf-8 -*-

import os
import json
from pathlib import Path

import config
from model_srv.mongodb.CategoryService import BackendCategory
from model_srv.mongodb.auth.AuthService import MongoAuthService
from utils.global_utils import get_hashed_password


there_path = Path(__file__)
project_path = os.path.join(os.path.dirname(there_path), '..')


def init_template_of_dirs():
    global project_path

    _dirs = [config.LOGGING_DIR, config.TABLE_PARTS_DIR]
    for _dir in _dirs:
        if not os.path.isdir(os.path.join(project_path, _dir)):
            os.makedirs(_dir, exist_ok=True)


def init_categories_to_db():
    global project_path

    BackendCategory.remove_all()
    with open(os.path.join(project_path, config.CATEGORIES_JSON), encoding='utf-8') as file:
        categories = json.load(file)

    for category in categories:
        category['model'] = 'all'
        back_cat = BackendCategory(**category)
        back_cat.insert_object()


def try_to_create_superuser():
    m = MongoAuthService()
    login_su = m.find_object({'role': 'superuser'}, multiple=False)
    if not login_su:
        m.insert_object({'login': 'admin', 'password': get_hashed_password('admin'), 'role': 'superuser'})
    m.close_connection()


if __name__ == '__main__':
    try_to_create_superuser()
    init_template_of_dirs()
    init_categories_to_db()
