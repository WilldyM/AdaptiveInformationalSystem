# -*- coding: utf-8 -*-
import json

import pandas as pd
import sqlalchemy
from sqlalchemy.sql.sqltypes import *

from components.SQLConnector.custom_forms.extract_form import SQLExtractForm
from components.SQLConnector.custom_forms.init_form import SQLInitForm
from components.SQLConnector.custom_forms.metadata_form import SQLMetadataForm
from model_srv.BaseComponent.BaseConnectorComponent import BaseConnectorComponent
from components.SQLConnector.Tableload import Tableload
from model_srv.mongodb.CObjectService import BackendCObject

"""

# Подключение к серверу MySQL на localhost с помощью PyMySQL DBAPI. 
engine = create_engine("mysql+pymysql://root:pass@localhost/mydb")

# Подключение к серверу MySQL по ip 23.92.23.113 с использованием mysql-python DBAPI. 
engine = create_engine("mysql+mysqldb://root:pass@23.92.23.113/mydb")

# Подключение к серверу PostgreSQL на localhost с помощью psycopg2 DBAPI 
engine = create_engine("postgresql+psycopg2://root:pass@localhost/mydb")

# Подключение к серверу Oracle на локальном хосте с помощью cx-Oracle DBAPI.
engine = create_engine("oracle+cx_oracle://root:pass@localhost/mydb"))

# Подключение к MSSQL серверу на localhost с помощью PyODBC DBAPI.
engine = create_engine("mssql+pyodbc://root:pass@localhost/mydb")

# Подключение к SQLite3
engine = create_engine('sqlite:////path/to/sqlite3.db')  # абсолютный путь

"""


class SQLConnection(BaseConnectorComponent):

    def __init__(self, bk_object: BackendCObject):
        self.bk_object = bk_object
        self.dev_drivers = {
            'pymysql': 'mysql',
            'psycopg2': 'postgresql',
            'cx_oracle': 'oracle',
            'pyodbc': 'mssql'
        }

        # init data for connect
        self._driver = bk_object.properties['driver']['value']
        self._server = bk_object.properties['server']['value']
        self._db = bk_object.properties['database']['value']
        self._user = bk_object.properties['username']['value']
        self._pw = bk_object.properties['password']['value']
        self.metamodel = None

        if bk_object.properties['port']['value'] == '':
            bk_object.properties['port']['value'] = None
        if bk_object.properties['port']['value'] is None:
            self._connect_args = dict(host=bk_object.properties.get('host', {}).get('value', None), port=None)
        else:
            self._connect_args = dict(host=bk_object.properties.get('host', {}).get('value', None),
                                      port=int(bk_object.properties['port']['value']))

        self._pyodbc_driver = 'ODBC+Driver+17+for+SQL+Server'
        if self._driver == 'pyodbc':
            self.conn_str = f'{self.dev_drivers[self._driver]}+{self._driver}://{self._user}:{self._pw}' \
                            f'@{self._server}/{self._db}' \
                            f'?driver={self._pyodbc_driver}'
        else:
            self.conn_str = f'{self.dev_drivers[self._driver]}+{self._driver}://{self._user}:{self._pw}' \
                            f'@{self._server}/{self._db}'

        self.engine = None
        self.table_columns = dict()
        self.queries = dict()
        self.data = dict()

    def get_projection(self, previous=None):
        self.build_queries(self.bk_object.properties['q_data']['value'])
        for table, query in self.queries.items():
            self.extract(table, query)
        result = list()
        for k, v in self.data.items():
            v['table_name'] = k
            result.append(v)
        return result

    def get_possible_values(self, _property) -> list:
        bk_category = self.bk_object.get_bk_category()
        for t in bk_category.template:
            if t['self_name'] == _property:
                return t['possible_values']
        return list()

    def init_form(self, model_form):
        form = SQLInitForm(model_form, self)
        form.show()

    def get_metadata(self, model_form):
        self.set_connection()
        metadata_sql = dict()
        inspector = sqlalchemy.inspect(self.engine)

        metadata_sql[self._db] = dict()
        for table_name in inspector.get_table_names():
            metadata_sql[self._db][table_name] = dict()
            for column in inspector.get_columns(table_name):
                metadata_sql[self._db][table_name][column['name']] = column

        metadata_sql = self.transform_mdt(metadata_sql)
        self.close_connection()
        form = SQLMetadataForm(model_form, self, metadata_sql)
        form.show()

    def build_queries(self, _q_data):
        if isinstance(_q_data, str):
            _q_data = json.loads(_q_data)
        r = dict()
        for db, tables in _q_data.items():
            if db == 'ТипБазы':
                continue
            for table, columns in tables.items():
                if not isinstance(columns, dict):
                    continue
                col_lst = list([col for col, val in columns.items() if isinstance(val, dict)])
                self.table_columns[table] = col_lst
                r[table] = self.create_query_from_db_dict(table, col_lst)

        self.queries = r
        return r

    def extract(self, tbl, query):
        self.set_connection()

        self.data[tbl] = list()
        new_tbl = list()
        for row in self.engine.execute(sqlalchemy.text(query)):
            new_row = dict()
            for i, val in enumerate(list(row)):
                new_row[self.table_columns[tbl][i]] = str(val)

            new_tbl.append(new_row)

        self.data[tbl] = json.loads(pd.DataFrame(new_tbl).to_json(orient='split'))

    def extract_all(self, model_form):
        self.build_queries(self.bk_object.properties['q_data']['value'])
        for table, query in self.queries.items():
            self.extract(table, query)

        form = SQLExtractForm(model_form, self, self.data)
        form.show()

    def __getstate__(self):
        self.engine = None

    def create_table(self, tbl_name: str, fields: dict):
        """
        EXAMPLE
        fields = {
            'FLD_NAME_1': {
                'type': 'BigInteger',
                'nullable': False,
                'primary_key': True
            },
            'FLD_NAME_2': {
                'type': 'String',
                'nullable': True,
                'primary_key': False
            }
        }
        """
        self.set_connection()
        meta = sqlalchemy.MetaData()

        tmp_table = sqlalchemy.Table(tbl_name, meta)

        for fld_name, fld_opt in fields.items():
            fld_obj = sqlalchemy.Column(fld_name, self.generic_types[fld_opt['type']],
                                        primary_key=fld_opt['primary_key'], nullable=fld_opt['nullable'])
            tmp_table.append_column(fld_obj)

        tmp_table.create(self.engine)

    def append_field_to_table(self, table_name: str, field_name: str, field_options: dict):
        self.set_connection()

        fld_obj = sqlalchemy.Column(field_name, self.generic_types[field_options['type']],
                                    primary_key=field_options['primary_key'],
                                    nullable=field_options['nullable'])

        column_name = fld_obj.compile(dialect=self.engine.dialect)
        column_type = fld_obj.type.compile(self.engine.dialect)
        self.engine.execute('ALTER TABLE %s ADD COLUMN %s %s' % (table_name, column_name, column_type))

    def load_tbl(self, tbl, table_name, field_map):
        self.set_connection()

        metadata = sqlalchemy.MetaData()
        metadata.reflect(bind=self.engine)
        table_obj = metadata.tables[table_name]
        p_keys = table_obj.primary_key.columns.values()

        primary_keys = []
        if len(p_keys) > 0:
            primary_keys = [p_k.name for p_k in p_keys]

        insert_queries = list()

        df = pd.DataFrame(tbl['data'], columns=tbl['columns'])
        df = Tableload.prepare_dataset_for_load(df, errors='coerce')

        if df is not False:
            for index, row in df.iterrows():
                line_mapped = {}
                for field, true_field in field_map.items():
                    line_mapped[true_field] = row[field]
                insert_query = sqlalchemy.insert(table_obj).values(line_mapped)

                try:
                    self.engine.execute(insert_query)
                except sqlalchemy.exc.IntegrityError as err:
                    # print(err)
                    insert_query = sqlalchemy.update(table_obj).where(
                        eval(self._build_condition_for_pk(primary_keys, line_mapped, table_obj))
                    ).values(line_mapped)
                    self.engine.execute(insert_query)
                insert_queries.append(str(insert_query.compile(compile_kwargs={"literal_binds": True})))
            return insert_queries
        else:
            raise Exception('Обнаружено несоответствие типов при выгрузке в БД')

    @staticmethod
    def _build_condition_for_pk(pk_lst: list, line_mapped: dict, table_obj):
        if len(pk_lst) > 1:
            r = 'and_('
            last_pk = pk_lst[-1]
            for pk in pk_lst[:-1]:
                try:
                    eval(f'table_obj.c.{pk} == line_mapped[\"{pk}\"]')
                    r += f'table_obj.c.{pk} == line_mapped[\"{pk}\"],'
                except KeyError:
                    continue
            try:
                eval(f'table_obj.c.{last_pk} == line_mapped[\"{last_pk}\"]')
                r += f'table_obj.c.{last_pk} == line_mapped[\"{last_pk}\"])'
            except KeyError:
                if r[-1] == '(':
                    r = ''

            if r[-1] == '(':
                r += ')'
        elif len(pk_lst) == 1:
            try:
                eval(f'table_obj.c.{pk_lst[0]} == line_mapped[\"{pk_lst[0]}\"]')
                r = f'table_obj.c.{pk_lst[0]} == line_mapped[\"{pk_lst[0]}\"]'
            except KeyError:
                r = ''
        else:
            r = ''
        return r

    @staticmethod
    def compile_columns(table_name, columns):
        columns = f"[{','.join([f'{table_name}.c.{col}' for col in columns])}]"
        return columns

    def create_query_from_db_dict(self, table_name: str, columns: list) -> str:
        self.set_connection()
        columns = self.compile_columns(table_name, columns)
        metadata = sqlalchemy.MetaData()
        metadata.reflect(bind=self.engine)
        exec(f'{table_name} = metadata.tables["{table_name}"]')
        query = str(sqlalchemy.select(eval(columns)))
        return query

    def transform_mdt(self, _mdt):
        r = [
            {
                'ИмяЭлемента': self._db,
                'ТипЭлемента': 'ИмяБазыДанных',
                'row': []
            }
        ]

        for table, columns in _mdt[self._db].items():
            table_dct = {
                'ИмяЭлемента': table,
                'ТипЭлемента': 'ИмяТаблицы',
                'row': []
            }
            r[0]['row'].append(table_dct)
            for col, col_props in columns.items():
                col_dct = {
                    'ИмяЭлемента': str(col),
                    'ТипЭлемента': str(col_props['type'])
                }
                table_dct['row'].append(col_dct)
        return r

    @staticmethod
    def get_drivers_for_users():
        drs = {
            'pymysql': '[MySQL]',
            'psycopg2': '[PostgreSQL]',
            'cx_oracle': '[Oracle]',
            'pyodbc': '[MSSQL]',
            'sqlite': '[SQLite3]'
        }
        return drs

    @property
    def generic_types(self):
        gt = {
            'BigInteger': BigInteger,
            'Boolean': Boolean,
            'Date': Date,
            'Time': Time,
            'DateTime': DateTime,
            'Float': Float,
            'Integer': Integer,
            'Interval': Interval,
            'LargeBinary': LargeBinary,
            'String': String,
            'Text': Text,
            'Unicode': Unicode,
            'UnicodeText': UnicodeText
        }
        return gt

    def set_connection(self):
        if not self.engine:
            self.engine = sqlalchemy.create_engine(self.conn_str, connect_args=self._connect_args,
                                                   encoding='utf8')

    def close_connection(self):
        self.engine.dispose()