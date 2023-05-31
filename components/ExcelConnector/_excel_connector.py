import os
import json
import pandas as pd
import numpy
import datetime
import config

from openpyxl import load_workbook

from model_srv.BaseComponent.BaseConnectorComponent import BaseConnectorComponent


class ExcelConnection(BaseConnectorComponent):

    def __init__(self, conn_prm: dict):
        self.username = conn_prm.get('username', '')
        self.base_dir = os.path.join(config.FTP_DIR, self.username)

        self.filename = conn_prm.get('filename', '')
        self.filename = self.filename.split(';')
        self.filename = [fn for fn in self.filename if fn != '']

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
    def get_export_data(md_obj):
        excel_dict = {
            'type': 'ftp_dir',
            'username': md_obj.properties['username'],
            'filename': []
        }
        if md_obj.properties['filename'] != "":
            excel_dict['filename'].append(md_obj.properties['filename'])

        return excel_dict

    def _get_filepath(self, fn):
        return os.path.join(self.base_dir, fn)

    def _get_tmp_filepath(self, fn):
        now = datetime.datetime.now()
        # now_datetime = now.strftime('%d_%m_%Y__%H_%M')
        now_datetime = now.strftime('%d_%m_%Y')
        return os.path.join(self.base_dir, f'{now_datetime}_{fn}')

    def load_tbl(self, tbl, table_name, field_map):
        if len(self.filename) > 1:
            return

        filepath = self._get_tmp_filepath(self.filename[0])

        # filepath = os.path.join(self.base_dir, self.filename[0])

        df = pd.DataFrame(tbl['data'], columns=tbl['columns'])
        for col in [col for col in df.columns if col not in field_map.keys()]:
            df.drop(col, axis=1, inplace=True)
        df.rename(columns=field_map, inplace=True)
        if not df.empty:
            df.to_excel(filepath, sheet_name=table_name, index=False, encoding='utf-8')

    def get_metadata(self):
        metadata_excel = list()
        for file in self.filename:
            filepath = self._get_filepath(file)

            workbook = load_workbook(filepath, read_only=True)
            data = {}
            for sheet in workbook.worksheets:
                for value in sheet.iter_rows(min_row=1, max_row=1, values_only=True):
                    data[sheet.title] = value

            metadata_excel.append(self.transform_mdt(data, file))

        return metadata_excel

    def build_queries(self, _q_data, preview_rows=0):
        if isinstance(_q_data, str):
            _q_data = json.loads(_q_data)
        r = dict()
        for filename, sheets in _q_data.items():
            if filename == 'ТипБазы':
                continue
            r[filename] = dict()
            if sheets is None:
                continue
            for sheet, columns in sheets.items():
                if not isinstance(columns, dict):
                    continue
                columns = {k: v for k, v in columns.items() if isinstance(v, dict)}
                r[filename][sheet] = columns

        self.queries = r
        self._preview_rows = preview_rows if preview_rows != 0 else None
        return r

    def read_and_processing(self, filepath, sheet_name, usecols=None, index_col=None):
        date_col_called = False
        if usecols:
            usecols = list(filter(lambda x: x is not None and x != 'null', usecols))

            for col_id in range(len(usecols)):
                try:
                    usecols[col_id] = datetime.datetime.strptime(usecols[col_id], '%Y-%m-%d %H:%M:%S')
                    date_col_called = True
                except ValueError:
                    continue
        if date_col_called:
            df = pd.read_excel(filepath, sheet_name=sheet_name, index_col=index_col)[usecols]
        else:
            df = pd.read_excel(filepath, sheet_name=sheet_name, index_col=index_col, usecols=usecols)
        excel_file = load_workbook(filename=filepath)
        sheet = excel_file[sheet_name]

        for r in sheet.merged_cells.ranges:
            cl, rl, cr, rr = r.bounds  # границы объединенной области
            rl -= 2
            rr -= 1
            cl -= 1
            base_value = df.iloc[rl, cl]
            df.iloc[rl:rr, cl:cr] = base_value

        if self._preview_rows:
            # df = df.head(self._preview_rows)

            filename = TMPFile.create_tmp_file(data=df)
            self.metamodel.tmp_files[filename] = TMPFile.get_iterator(filename, size=100, is_df=False)
            return_data = TMPFile.next(self.metamodel.tmp_files[filename])
        else:
            for col, t in zip(df.dtypes.index, df.dtypes):
                # if t in ['datetime64[ns]', 'timedelta64[ns]']:
                if any(i for i in df[col] if isinstance(i, datetime.datetime) or isinstance(i, datetime.timedelta)):
                    df[col] = df[col].astype('str')

            df.replace(numpy.nan, 'NaN', inplace=True)

            return_data = json.loads(df.to_json(orient='split'))

        return return_data

    def extract(self, fn_sheet, columns, dont_change_answer=False):
        filepath = self._get_filepath(fn_sheet[0])
        return_data = self.read_and_processing(filepath, sheet_name=fn_sheet[1], usecols=list(columns.keys()), index_col=None)
        self.data[fn_sheet[1]] = return_data

    def extract_all(self, dont_change_answer=False, metamodel=None):
        self.metamodel = metamodel
        for filename, sheet_columns in self.queries.items():
            for sheet, columns in sheet_columns.items():
                self.extract((filename, sheet), columns, dont_change_answer)

    def transform_mdt(self, _data, _fn):
        r = {
            'ИмяЭлемента': _fn,
            'ТипЭлемента': 'ИмяФайла',
            'row': []
        }
        for sheet, columns in _data.items():
            rows = list()
            for col in columns:
                if isinstance(col, datetime.datetime):
                    col = col.strftime('%Y-%m-%d %H:%M:%S')
                row_dct = {
                    'ИмяЭлемента': col,
                    'ТипЭлемента': 'ИмяКолонки'
                }
                rows.append(row_dct)

            sheet_dct = {
                'ИмяЭлемента': sheet,
                'ТипЭлемента': 'ИмяЛиста',
                'row': rows
            }
            r['row'].append(sheet_dct)
        return r


def test():
    excel_connector = ExcelConnection(dict(username='guest', filename=['excel_file_1.xlsx', 'excel_file_2.xlsx']))
    print(excel_connector.get_metadata())


def main():
    field_map = {
        '_Наименование': 'Наименование',
        '_Артикул': 'Артикул',
    }

    tbl = [
        {
            '_Наименование': 'А ЭТО НОВЫЙ АРТИКУЛ ОХАЙО',
            '_Артикул': 'ЭТО НОВОЕ НАИМЕНОВАНИЕ_1',
        }
    ]
    excel_connector = ExcelConnection(dict(username='root', filename='Номенклатура.xlsx'))
    excel_connector.load_tbl(tbl, 'TDSheet', field_map)


if __name__ == '__main__':
    test()