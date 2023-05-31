import os
import datetime
import json
import numpy
import pandas as pd
import config

from model_srv.BaseComponent.BaseConnectorComponent import BaseConnectorComponent
from model_srv.TMPFile import TMPFile


class CSVConnection(BaseConnectorComponent):

    def __init__(self, conn_prm: dict):
        self.username = conn_prm.get('username', '')
        self.base_dir = os.path.join(config.FTP_DIR, self.username)

        self.filename = conn_prm.get('filename', '')
        self.delimiter = conn_prm['delimiter'] if conn_prm['delimiter'] != '' else ','
        self.queries = dict()
        self.data = dict()
        self.metamodel = None

        self._preview_rows = None

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
    def specified_possible_out_values_from_extraction(q_data, opv):
        for tbl_name, tbl_prop in q_data.items():
            if tbl_name == 'queries':
                opv.update({tbl_name: tbl_name for tbl_name in tbl_prop.keys()})
                continue
            if isinstance(tbl_prop, dict):
                opv[tbl_name] = tbl_name
        return opv

    @staticmethod
    def get_export_data(md_obj):
        csv_dict = {
            'type': 'ftp_dir',
            'username': md_obj.properties['username'],
            'filename': []
        }
        if md_obj.properties['filename'] != "":
            csv_dict['filename'].append(md_obj.properties['filename'])

        return csv_dict

    def _get_filepath(self):
        return os.path.join(self.base_dir, self.filename)

    def _get_tmp_filepath(self):
        now = datetime.date.today()
        now_date = now.strftime('%d_%m_%Y')
        return os.path.join(self.base_dir, f'{now_date}_{self.filename}')

    def load_tbl(self, tbl, table_name, field_map):
        filepath = self._get_tmp_filepath()
        # df = pd.DataFrame()

        # for line in tbl:
        #     line_mapped = dict()
        #     for field, true_field in field_map.items():
        #         if line.get(field):
        #             line_mapped[true_field] = line[field]
        #     line_df = pd.DataFrame([line_mapped])
        #     df = pd.concat([df, line_df], ignore_index=True, sort=False)

        df = pd.DataFrame(tbl['data'], columns=tbl['columns'])
        for col in [col for col in df.columns if col not in field_map.keys()]:
            df.drop(col, axis=1, inplace=True)
        df.rename(columns=field_map, inplace=True)

        df.to_csv(filepath, index=False, encoding='cp1251')  # cp1251 cuz MSExcel cant read csv with utf-8
        # df.to_csv(filepath, index=False, encoding='utf-8')  # cp1251 cuz MSExcel cant read csv with utf-8

    def build_queries(self, _q_data, preview_rows=0):
        if isinstance(_q_data, str):
            _q_data = json.loads(_q_data)
        r = dict()
        for filename, columns in _q_data.items():
            if filename == 'ТипБазы':
                continue
            r[filename] = {k: v for k, v in columns.items() if isinstance(v, dict)}

        self.queries = r
        self._preview_rows = preview_rows if preview_rows != 0 else None
        return r

    def _read_csv(self, filepath, usecols, nrows, encoding):
        df = None
        return_data = None
        if encoding:
            try:
                if nrows is None:
                    df = pd.read_csv(filepath, index_col=None, delimiter=self.delimiter,
                                     encoding=encoding[0], usecols=usecols, low_memory=False)
                    df.replace(numpy.nan, 'NaN', inplace=True)

                    for col, t in zip(df.dtypes.index, df.dtypes):
                        if t in ['datetime64[ns]', 'timedelta64[ns]']:
                            df[col] = df[col].astype('str')

                    return_data = json.loads(df.to_json(orient='split'))

                else:
                    df = pd.read_csv(filepath, index_col=None, delimiter=self.delimiter,
                                     encoding=encoding[0], usecols=usecols, low_memory=False)

                    filename = TMPFile.create_tmp_file(data=df)
                    self.metamodel.tmp_files[filename] = TMPFile.get_iterator(filename, size=100, is_df=False)
                    return_data = TMPFile.next(self.metamodel.tmp_files[filename])
            except Exception as err:
                print(err)
                return_data = self._read_csv(filepath, usecols, nrows, encoding[1:])
            finally:
                if isinstance(df, pd.DataFrame):
                    return return_data
                else:
                    raise Exception('The CSV file was not loaded')
        else:
            raise Exception('The CSV file was not loaded')

    def extract(self, filename, columns, dont_change_answer=False):
        filepath = self._get_filepath()

        return_data = self._read_csv(filepath=filepath, usecols=list(columns.keys()), nrows=self._preview_rows,
                                     encoding=['utf-8', 'cp1251', 'cp1252', 'latin-1', 'iso_8859_1'])

        # df.replace(numpy.nan, 'NaN', inplace=True)
        #
        # for col, t in zip(df.dtypes.index, df.dtypes):
        #     if t in ['datetime64[ns]', 'timedelta64[ns]']:
        #         df[col] = df[col].astype('str')

        # df_dict = df.to_dict('records')
        self.data[filename] = return_data

    def extract_all(self, dont_change_answer=False, metamodel=None):
        self.metamodel = metamodel
        for filename, columns in self.queries.items():
            self.extract(filename, columns, dont_change_answer)

    def get_metadata(self):
        filepath = self._get_filepath()
        try:
            csv_df = pd.read_csv(filepath, delimiter=self.delimiter, low_memory=False)
        except UnicodeDecodeError:
            csv_df = pd.read_csv(filepath, delimiter=self.delimiter, low_memory=False, encoding='cp1251')
        metadata_csv = self.transform_mdt(csv_df)
        return metadata_csv

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


if __name__ == '__main__':
    conn_prm = {
        'username': 'root',
        'filename': 'mosautoshina_price_tyre.csv',
        'delimiter': ','
    }
    csv_con = CSVConnection(conn_prm)
    print(csv_con.get_metadata())
