# -*- coding: utf-8 -*-
import json

import pandas as pd
import sqlalchemy
from sqlalchemy.sql.sqltypes import *

from model_srv.BaseComponent.BaseConnectorComponent import BaseConnectorComponent
from model_srv.utils.Tableload import Tableload
from model_srv.TMPFile import TMPFile

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

    def __init__(self, conn_prm: dict):
        self.dev_drivers = {
            'pymysql': 'mysql',
            'psycopg2': 'postgresql',
            'cx_oracle': 'oracle',
            'pyodbc': 'mssql'
        }

        # init data for connect
        self._driver = conn_prm.get('driver')
        self._server = conn_prm.get('server')
        self._db = conn_prm.get('database')
        self._user = conn_prm.get('username')
        self._pw = conn_prm.get('password')
        self._trusted_connection = conn_prm.get('trusted_connection', False)
        self.metamodel = None

        if conn_prm.get('port') == '':
            conn_prm['port'] = None
        if conn_prm['port'] is None:
            self._connect_args = dict(host=conn_prm.get('host'), port=None)
        else:
            self._connect_args = dict(host=conn_prm.get('host'), port=int(conn_prm.get('port')))

        self._pyodbc_driver = 'ODBC+Driver+17+for+SQL+Server'
        if self._trusted_connection == 'True' or self._trusted_connection is True:
            self.conn_str = f'{self.dev_drivers[self._driver]}+{self._driver}://' \
                            f'@{self._server}/{self._db}?trusted_connection=yes' \
                            f'&driver={self._pyodbc_driver}'
        else:
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
        self._preview_rows = None

    def __getstate__(self):
        self.engine = None

    def from_extraction_to_data_space(self, ext_data, extr_obj, mdt_obj, data_space, container):
        another_res = dict()
        for t, col_val in ext_data.items():
            table = t.replace(' ', '_')
            changed_columns = [col.replace(' ', '_') for col in col_val['columns']]
            fields = data_space.add_df_to_model(pd.DataFrame(col_val['data'], columns=changed_columns),
                                                table)
            tbl_obj = extr_obj.add_table(table, fields, mdt_obj.metamodel)
            tbl_obj.properties['data_space'] = data_space.name
            if container:
                container.properties['tables'][table] = tbl_obj.properties['fields']
            else:
                another_res[table] = tbl_obj.properties['fields']

        return another_res

    @staticmethod
    def get_export_data(md_obj):
        return None

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

    def extract(self, tbl, query, dont_change_answer=False):
        self.set_connection()

        self.data[tbl] = list()
        new_tbl = list()
        for row in self.engine.execute(sqlalchemy.text(query)):
            new_row = dict()
            for i, val in enumerate(list(row)):
                new_row[self.table_columns[tbl][i]] = str(val)

            new_tbl.append(new_row)

        if self._preview_rows:
            filename = TMPFile.create_tmp_file(data=new_tbl)
            self.metamodel.tmp_files[filename] = TMPFile.get_iterator(filename, size=100, is_df=False)
            next_iter = TMPFile.next(self.metamodel.tmp_files[filename])
            if not next_iter:
                next_iter = {
                    'data': [],
                    'columns': self.table_columns[tbl]
                }
            self.data[tbl] = next_iter
        else:
            self.data[tbl] = json.loads(pd.DataFrame(new_tbl).to_json(orient='split'))

    def extract_all(self, dont_change_answer=False, metamodel=None):
        self.metamodel = metamodel
        for table, query in self.queries.items():
            self.extract(table, query, dont_change_answer)

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
        if self._preview_rows:
            query = str(sqlalchemy.select(eval(columns))) + f' LIMIT {self._preview_rows}'
        else:
            query = str(sqlalchemy.select(eval(columns)))
        return query

    def build_queries(self, _q_data, preview_rows=0):
        if isinstance(_q_data, str):
            _q_data = json.loads(_q_data)
        r = dict()
        self._preview_rows = preview_rows if preview_rows != 0 else None
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

    def get_metadata(self):
        self.set_connection()
        metadata_sql = dict()
        inspector = sqlalchemy.inspect(self.engine)
        # schemas = inspector.get_schema_names()

        metadata_sql[self._db] = dict()
        # for schema in schemas:
        #     metadata_sql[self._db][schema] = dict()
        for table_name in inspector.get_table_names():
            metadata_sql[self._db][table_name] = dict()
            for column in inspector.get_columns(table_name):
                metadata_sql[self._db][table_name][column['name']] = column

        metadata_sql = self.transform_mdt(metadata_sql)
        self.close_connection()
        return metadata_sql

    def transform_mdt(self, _mdt):  # mojet kogda-nibud' sdelayu universalniy method...
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
                # for col_prop_key, col_prop_val in col_props.items():
                #     if col_prop_key in ['nullable', 'default', 'autoincrement', 'comment']:
                #         continue
                #     col_prop_dct = {
                #         'ИмяЭлемента': str(col_prop_key),
                #         'ТипЭлемента': str(col_prop_val)
                #     }
                #     col_dct['row'].append(col_prop_dct)
        return r


def main_test_metadata():
    prms = {
        'driver': 'psycopg2',
        'server': 'localhost',
        'database': 'Michelin',
        'username': 'postgres',
        'password': 'admin',
        'port': 5432,
        'trusted_connection': False
    }
    prms = {
        'driver': 'pyodbc',
        'server': 'DESKTOP-UDMTB5K\\SQLEXPRESS',
        'database': 'Michelin',
        'username': 'sa',
        'password': 'Шпщк11235',
        'port': None,
        'trusted_connection': False
    }
    sqlcon = SQLConnection(prms)
    print(sqlcon.conn_str)
    print(sqlcon.get_metadata()[0])


def append_field_test_main():
    prms = {
        'driver': 'psycopg2',
        'server': 'localhost',
        'database': 'Michelin',
        'username': 'postgres',
        'password': 'admin',
        'port': None,
        'trusted_connection': False
    }
    sqlcon = SQLConnection(prms)
    field_opt = {
        'type': 'Date',
        'nullable': True,
        'primary_key': False
    }
    sqlcon.append_field_to_table('new_table', 'NEW_FIELD', field_opt)


def create_table_main():
    prms = {
        'driver': 'psycopg2',
        'server': 'localhost',
        'database': 'Michelin',
        'username': 'postgres',
        'password': 'admin',
        'port': None,
        'trusted_connection': False
    }
    sqlcon = SQLConnection(prms)
    fields = {
        'partner_id': {
            'type': 'Integer',
            'nullable': False,
            'primary_key': True
        },
        'date': {
            'type': 'Date',
            'nullable': True,
            'primary_key': False
        }
    }
    sqlcon.create_table('sec_sales', fields)


def main():
    prms = {
        'driver': 'psycopg2',
        'server': 'localhost',
        'database': 'Michelin',
        'username': 'postgres',
        'password': 'admin',
        'port': None,
        'trusted_connection': False
    }

    field_map = {
        'id': 'id',
        'Имя': 'first_name',
        'Фамилия': 'last_name',
        'Пол': 'gender',
        'Почта': 'email',
        'Дата рождения': 'date_of_birth',
    }

    tbl = [
        {
            'id': 22,
            'Имя': 'Игорь_Updated',
            'Фамилия': 'Геша',
            'Пол': 'М',
            'Почта': 'example_igor@example.com',
            'Дата рождения': '2000-11-03'
        }
    ]

    sqlcon = SQLConnection(prms)
    print(sqlcon.load_tbl(tbl, 'employee', field_map))


def sec_sales_test():
    prms = {
        'driver': 'psycopg2',
        'server': 'localhost',
        'database': 'Michelin',
        'username': 'postgres',
        'password': 'admin',
        'port': None,
        'trusted_connection': False
    }

    field_map = {
        'partner_id': 'partner_id',
        'datetime': 'datetime',
        'item': 'item',
        'x_code': 'x_code',
        'doc_num': 'doc_num',
        'reservation_number': 'reservation_number',
        'mk': 'mk',
        'trading_place': 'trading_place',
        'disc': 'disc',
        'article_number': 'article_number',
        'item_name': 'item_name',
        'operation_type': 'operation_type',
        'price': 'price',
        'price_disc': 'price_disc',
        'qty': 'qty',
        'amount': 'amount',
        'amount_disc': 'amount_disc',
        'saler': 'saler'
    }

    tbl = [
        {
            'partner_id': 48268,
            'datetime': '2022-11-26 15:12:59.000',
            'item': None,
            'x_code': 'Х0122505',
            'doc_num': None,
            'reservation_number': None,
            'mk': None,
            'trading_place': 'Новый',
            'disc': None,
            'article_number': None,
            'item_name': 'Обувь ортопедическая Berkemann Linette р.39,5 (6) черный/серый',
            'operation_type': 'Продажа',
            'price': None,
            'price_disc': 15.00,
            'qty': 3.00,
            'amount': None,
            'amount_disc': None,
            'saler': 'Четверикова Елена Николаевна'
        }
    ]

    sqlcon = SQLConnection(prms)
    print(sqlcon.load_tbl(tbl, 'sec_sales', field_map))


if __name__ == '__main__':
    sec_sales_test()
