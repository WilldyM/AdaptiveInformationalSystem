import pandas as pd
from pandas.errors import ParserError
import re


class Tableload(object):

    @staticmethod
    def check_patterns(value):
        patterns = [
            {
                'pattern': r'^[0-9]{2}\.[0-9]{2}\.[0-9]{2}$',
                'format': "%d.%m.%y"
            },
            {
                'pattern': r'^[0-9]{2}\.[0-9]{2}\.[0-9]{4}$',
                'format': "%d.%m.%Y"
            },
            {
                'pattern': r'^[0-9]{2}\/[0-9]{2}\/[0-9]{4}$',
                'format': "%d/%m/%Y"
            },
            {
                'pattern': r'^[0-9]{2}\/[0-9]{2}\/[0-9]{2}$',
                'format': "%d/%m/%y"
            }
        ]
            
        for pattern in patterns:
            find = re.match(pattern['pattern'], str(value).strip())
            if find:
                return {
                    'success': True,
                    'format': pattern['format']
                }
        return False

    @staticmethod
    def convert_date(x, format='', errors='raise'):
        try:
            return pd.to_datetime(x, dayfirst=True, format=format, exact=True, errors=errors)
        
        except Exception as e:
            # print('error_desc', x)
            raise Exception(e)

    @staticmethod
    def is_date_column(data_column):
        item = data_column[data_column.notna()].iloc[0]

        if isinstance(item, str):
            item = item.strip()
            # print('item', item)
            return Tableload.check_patterns(item)

    @staticmethod
    def get_date_columns(ds):
        date_columns = {}
        for col_name in ds.columns:
            ds[col_name].replace('NaN', None, inplace=True)
            res = Tableload.is_date_column(ds[col_name])
            if res:
                date_columns[col_name] = res['format']
        return date_columns

    @staticmethod
    def convert_date_values_in_dataset(ds, date_columns, errors='coerce'):
        for col_name in date_columns:
            # print(col_name, date_columns[col_name])
            ds[col_name] = ds[col_name].apply(lambda x: Tableload.convert_date(x, format=date_columns[col_name], errors=errors))
        return ds

    @staticmethod
    def clean_data(ds, date_columns):
        for col_name in date_columns:
            # nanValues = ds[col_name].isna()
            # print(col_name, nanValues)
            # print()
            # print(col_name, ds[nanValues])
            # print()
            ds = ds[ds[col_name].notna()]
        return ds
    
    @staticmethod
    def prepare_dataset_for_load(ds, errors='raise'):
        """
        errors{`ignore`, `raise`, `coerce`}, default `raise`
        If 'raise', then invalid parsing will raise an exception.
        If 'coerce', then invalid parsing will be set as NaT.
        """
        try:
            date_columns = Tableload.get_date_columns(ds)
            # print(date_columns)

            ds = Tableload.convert_date_values_in_dataset(ds, date_columns, errors=errors)
            # print(ds)
            # print()

            ds = Tableload.clean_data(ds, date_columns)
            # print(ds)

            return ds
        except Exception as e:
            print('prepare_dataset_for_load', e)
            return False
