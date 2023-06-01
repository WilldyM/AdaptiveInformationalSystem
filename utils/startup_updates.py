import os
import json

import config
from model_srv.mongodb.CategoryService import BackendCategory
from model_srv.mongodb.auth.AuthService import MongoAuthService
from utils.global_utils import get_hashed_password


def init_template_of_dirs():
    _dirs = [config.LOGGING_DIR, config.TABLE_PARTS_DIR]
    for _dir in _dirs:
        if not os.path.isdir(_dir):
            os.makedirs(_dir, exist_ok=True)


def init_categories_to_db():
    BackendCategory.remove_all()
    with open(config.CATEGORIES_JSON) as file:
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
