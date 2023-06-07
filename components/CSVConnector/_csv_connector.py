import os
import datetime
import json
import numpy
import pandas as pd
import config

from model_srv.BaseComponent.BaseConnectorComponent import BaseConnectorComponent
from model_srv.mongodb.CObjectService import BackendCObject

from components.CSVConnector.custom_forms.init_form import CSVInitForm
from components.CSVConnector.custom_forms.metadata_form import CSVMetadataForm
from components.CSVConnector.custom_forms.extract_form import CSVExtractForm


class CSVConnection(BaseConnectorComponent):

    def __init__(self, bk_object: BackendCObject):
        self.bk_object = bk_object
        if bk_object.properties['filename']['value']:
            self.filename = os.path.basename(bk_object.properties['filename']['value'])
        else:
            self.filename = ''
        if bk_object.properties['filename']['value']:
            self.base_dir = os.path.dirname(bk_object.properties['filename']['value'])
        else:
            self.base_dir = ''
        if bk_object.properties['delimiter']['value']:
            self.delimiter = bk_object.properties['delimiter']['value']
        else:
            self.delimiter = ','
        self.queries = dict()
        self.data = dict()

    def get_projection(self, previous=None):
        self.build_queries(self.bk_object.properties['q_data']['value'])
        for filename, columns in self.queries.items():
            self.extract(filename, columns)
        return self.data

    def get_possible_values(self, _property) -> list:
        bk_category = self.bk_object.get_bk_category()
        for t in bk_category.template:
            if t['self_name'] == _property:
                return t['possible_values']
        return list()

    def init_form(self, model_form):
        form = CSVInitForm(model_form, self)
        form.show()

    def get_metadata(self, model_form):
        filepath = self._get_filepath()
        try:
            csv_df = pd.read_csv(filepath, delimiter=self.delimiter, low_memory=False)
        except UnicodeDecodeError:
            csv_df = pd.read_csv(filepath, delimiter=self.delimiter, low_memory=False, encoding='cp1251')
        metadata_csv = self.transform_mdt(csv_df)
        form = CSVMetadataForm(model_form, self, metadata_csv)
        form.show()

    def transform_mdt(self, _df):
        r = [
            {
                'ИмяЭлемента': self.filename,
                'ТипЭлемента': 'ИмяФайла',
                'row': []
            }
        ]
        for col in _df.columns:
            row_dct = {
                'ИмяЭлемента': col,
                'ТипЭлемента': 'ИмяКолонки'
            }
            r[0]['row'].append(row_dct)
        return r

    def _read_csv(self, filepath, usecols, encoding):
        df = None
        return_data = None
        if encoding:
            try:
                df = pd.read_csv(filepath, index_col=None, delimiter=self.delimiter,
                                 encoding=encoding[0], usecols=usecols, low_memory=False)
                df.replace(numpy.nan, 'NaN', inplace=True)

                for col, t in zip(df.dtypes.index, df.dtypes):
                    if t in ['datetime64[ns]', 'timedelta64[ns]']:
                        df[col] = df[col].astype('str')

                return_data = json.loads(df.to_json(orient='split'))
            except Exception as err:
                print(err)
                return_data = self._read_csv(filepath, usecols, encoding[1:])
            finally:
                if isinstance(df, pd.DataFrame):
                    return return_data
                else:
                    raise Exception('The CSV file was not loaded')
        else:
            raise Exception('The CSV file was not loaded')

    def build_queries(self, _q_data):
        if isinstance(_q_data, str):
            _q_data = json.loads(_q_data)
        r = dict()
        for filename, columns in _q_data.items():
            r[filename] = {k: v for k, v in columns.items() if isinstance(v, dict)}

        self.queries = r
        return r

    def extract(self, filename, columns):
        filepath = self._get_filepath()

        return_data = self._read_csv(filepath=filepath, usecols=list(columns.keys()),
                                     encoding=['utf-8', 'cp1251', 'cp1252', 'latin-1', 'iso_8859_1'])
        self.data[filename] = return_data

    def extract_all(self, model_form):
        self.build_queries(self.bk_object.properties['q_data']['value'])
        for filename, columns in self.queries.items():
            self.extract(filename, columns)

        form = CSVExtractForm(model_form, self, self.data)
        form.show()

    def load_tbl(self, tbl, table_name, field_map):
        filepath = self._get_tmp_filepath()

        df = pd.DataFrame(tbl['data'], columns=tbl['columns'])
        for col in [col for col in df.columns if col not in field_map.keys()]:
            df.drop(col, axis=1, inplace=True)
        df.rename(columns=field_map, inplace=True)

        df.to_csv(filepath, index=False, encoding='cp1251')  # cp1251 cuz MSExcel cant read csv with utf-8

    def _get_filepath(self):
        return os.path.join(self.base_dir, self.filename)

    def _get_tmp_filepath(self):
        now = datetime.date.today()
        now_date = now.strftime('%d_%m_%Y')
        return os.path.join(self.base_dir, f'{now_date}_{self.filename}')
