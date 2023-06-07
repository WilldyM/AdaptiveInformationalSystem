import os
import tempfile

import pandas as pd
import json
import numpy as np

from components.RelationalData.custom_forms.load_data import TableLoadDataForm
from desktop_version.pyside6.messages.messagebox import MessageError, MessageInfo
from model_srv.BaseComponent.BaseDataComponent import BaseDataComponent
from model_srv.mongodb.CObjectService import BackendCObject

import config


class RlTable(BaseDataComponent):
    def __init__(self, bk_object: BackendCObject):
        self.base_dir = config.TABLE_PARTS_DIR
        self.bk_object = bk_object
        self.cache_table = bk_object.properties['cache_table']['value']

    def read_feather(self, change_answer=False):
        if self.cache_table:
            try:
                tmp_path = os.path.join(self.base_dir, self.cache_table)
                df = pd.read_feather(tmp_path)
                if change_answer:
                    df.replace([np.inf, -np.inf], np.nan, inplace=True)
                    df.replace(np.nan, 'NaN', inplace=True)
                table_data = json.loads(df.to_json(orient='split'))
                table_data.pop('index')
                return table_data
            except Exception as err:
                MessageError('Таблица', f'Traceback:\n{err}')
                self.cache_table = self.bk_object.properties['cache_table']['value'] = None
        else:
            MessageInfo('Таблица', 'Нет сохраннёной таблицы')
        return None

    def get_projection(self, previous):
        if not previous:
            return self.read_feather()
        else:
            self._update_table(model_form=None, previous=previous)
            return self.read_feather()

    def show_table(self, model_form, previous=None):
        if not previous:
            self._show_table(model_form)
        else:
            self._update_table(model_form, previous)

    def _show_table(self, model_form):
        table_data = self.read_feather(change_answer=True)
        if table_data is not None:
            form = TableLoadDataForm(model_form, self, {self.bk_object.display_name: table_data})
            form.show()

    def _update_table(self, model_form=None, previous: dict = None):
        tmpname = RlTable.get_unique_filename(path=self.base_dir)
        tmp_path = os.path.join(self.base_dir, tmpname)
        try:
            prev_key = list(previous.keys())[0]
            prev = previous.pop(prev_key)
            _df = pd.DataFrame(data=prev['data'], columns=prev['columns'])
            _df.replace([np.inf, -np.inf], np.nan, inplace=True)
            _df.replace('NaN', np.nan, inplace=True)
            _df.to_feather(tmp_path)
        except:
            for _ in _df.select_dtypes(include=['object']).columns:
                _df[_] = _df[_].astype('str')
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            _df.to_feather(tmp_path)

        if isinstance(_df, pd.DataFrame):
            self.bk_object.properties['cache_table']['value'] = self.cache_table = tmpname
            self.bk_object.update_object()
            if model_form is not None:
                self._show_table(model_form)

    @staticmethod
    def get_unique_filename(path: str, prefix: str = '', extension: str = ''):
        while True:
            tmp = prefix + next(tempfile._get_candidate_names()) + extension
            if not os.path.isfile(os.path.join(path, tmp)):
                return tmp
