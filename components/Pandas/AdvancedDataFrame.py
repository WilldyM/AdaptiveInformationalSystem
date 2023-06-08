import datetime
from pathlib import Path
import os
import copy
import tempfile
import json

from fastnumbers import fast_real
import pandas as pd
import numpy as np

import config
from components.Pandas.custom_forms.operands_form import OperandsForm
from desktop_version.pyside6.messages.messagebox import MessageInfo, MessageError

from model_srv.BaseComponent.BaseDataComponent import BaseDataComponent
from model_srv.mongodb.CObjectService import BackendCObject
from utils import global_utils as gl


class AdvancedDataFrame(BaseDataComponent):

    def __init__(self, bk_object: BackendCObject, previous=None):
        self.bk_object = bk_object
        self.tables = dict()
        self.options = dict()
        self._date_cols = dict()
        self.tmp_calculated = {'tables': [], 'fields': []}
        self.tried_to_calculate = dict()
        self.columns_id = {}

        self.table_df = None

        if bk_object.properties['operands']['value']:
            self.operands = bk_object.properties['operands']['value']
        else:
            self.operands = {}

        if self.operands.get('main_mapper') is None:
            self.operands['main_mapper'] = {}

        if not self.tables:
            self._init_tables(previous=previous)

        self.update_from_mapper()
        if not isinstance(self.operands, dict) or self.operands.get('tables') is None:
            self.operands['tables'] = {}
            self._init_new_operands()
        else:
            self._init_old_operands()

        self.update_user_tables_fields_to_mapper()

        self._update_fields()

        self._init_options()
        self._save_operands(self.operands)

    def get_projection(self, previous=None):
        result_tables = list()
        for tbl_name in self.operands['tables'].keys():
            result_tables.append(self.refresh_data(None, tbl_name))
        return result_tables

    def load_options(self, model_form, previous=None):
        if not previous:
            MessageInfo('DataFrame', 'На входе нет данных')
            return
        r = {
            'operands': self.update_possible_values(),
            'functions': self.options['functions']
        }
        form = OperandsForm(model_form, options=r)
        form.show()

    def update_from_mapper(self):
        for src_tbl, src_tbl_opt in self.operands['main_mapper'].items():
            _tbl_from = src_tbl_opt['source_self_name']
            _tbl_to = src_tbl_opt['current_self_name']
            _fields_from = [fld['source_self_name'] for fld in src_tbl_opt['fields'].values()]
            _fields_to = [fld['current_self_name'] for fld in src_tbl_opt['fields'].values()]
            if self.tables.get(_tbl_from) is None:
                continue
            self.tables[_tbl_from].rename(columns=dict(zip(_fields_from, _fields_to)), inplace=True)
            self.tables[_tbl_to] = self.tables.pop(_tbl_from)
            p = (2, {'type': 'Таблица'})
            p2 = {'type': 'Таблица'}
            self.operands['tables'] = \
                gl.dict_inner_rename_value(self.operands.get('tables', {}), _tbl_to, _tbl_from, 'self_name', pattern=p)
            self.operands['tables'] = \
                gl.dict_inner_rename_key(self.operands.get('tables', {}), _tbl_from, _tbl_to, inner_pattern=p2)

    def update_user_tables_fields_to_mapper(self):
        """
        Просто обновляем маппер из пользовательских таблиц,
        т.к. источником этих таблиц и является форма АДФ
        """
        tables_not_is_in = {t: opt for t, opt in self.operands['tables'].items()
                            if opt['is_in'] is False and not opt.get('hidden') is True}
        current_names_of_mapper = {v['current_self_name']: v for v in self.operands['main_mapper'].values()}
        for tbl, opt in tables_not_is_in.items():
            if tbl not in current_names_of_mapper.keys():
                self.operands['main_mapper'][tbl] = {
                    'source_self_name': opt['self_name'],
                    'current_self_name': opt['self_name'],
                    'display_name': opt['display_name'],
                    'fields': {}
                }
                self.update_user_fields_to_mapper(tbl, opt['fields'])
            else:
                tbl = current_names_of_mapper[tbl]['source_self_name']
                self.update_user_fields_to_mapper(tbl, opt['fields'])

        # Теперь обновим пользовательские поля в таблицах с другим источником
        table_is_in = {t: opt for t, opt in self.operands['tables'].items() if opt['is_in'] is True}
        for tbl, opt in table_is_in.items():
            for k, v in self.operands['main_mapper'].items():
                if v['current_self_name'] == tbl:
                    self.operands['main_mapper'][k]['display_name'] = opt['display_name']
                    temp_is_in_fields = dict()
                    for fld, fld_opt in self.operands['tables'][tbl]['fields'].items():
                        if fld_opt['is_in'] is False:
                            temp_is_in_fields[fld] = {
                                'source_self_name': fld_opt['self_name'],
                                'current_self_name': fld_opt['self_name'],
                                'display_name': fld_opt['display_name']
                            }
                        else:
                            for fk, fv in self.operands['main_mapper'][k]['fields'].items():
                                if fv['current_self_name'] == fld:
                                    temp_is_in_fields[fk] = {
                                        'source_self_name': self.operands['main_mapper'][k]['fields'][fk][
                                            'source_self_name'],
                                        'current_self_name': self.operands['main_mapper'][k]['fields'][fk][
                                            'current_self_name'],
                                        'display_name': fld_opt['display_name']
                                    }
                                    break
                    self.operands['main_mapper'][k]['fields'] = temp_is_in_fields
                    break

    def update_user_fields_to_mapper(self, tbl, fields):
        current_names_of_mapper = {v['current_self_name']: v for v in self.operands['main_mapper'][tbl]['fields'].values()}
        exists_fields = []
        for fld, opt in fields.items():
            if fld not in current_names_of_mapper.keys():
                temp_fld_opt = {
                    'source_self_name': opt['self_name'],
                    'current_self_name': opt['self_name'],
                    'display_name': opt['display_name']
                }
                self.operands['main_mapper'][tbl]['fields'][fld] = temp_fld_opt
                current_names_of_mapper[fld] = temp_fld_opt
            exists_fields.append(current_names_of_mapper[fld]['source_self_name'])

        for k, v in self.operands['main_mapper'][tbl]['fields'].copy().items():
            if k not in exists_fields:
                self.operands['main_mapper'][tbl]['fields'].pop(k)

    def _init_new_operands(self):
        for k, v in self.tables.items():
            current_tbl_name = k
            for col in v.columns:
                current_field_name = self.operands['main_mapper'][k]['fields'][col]['current_self_name']
                self.operands['tables'].setdefault(current_tbl_name, dict()).setdefault(
                    'fields', dict())[current_field_name] = {
                    'self_name': current_field_name,
                    'display_name': col,
                    'type': 'Поле',
                    'is_in': True,
                    'expression': {}
                }

            self.operands['tables'][current_tbl_name]['self_name'] = current_tbl_name
            self.operands['tables'][current_tbl_name]['display_name'] = k
            self.operands['tables'][current_tbl_name]['type'] = 'Таблица'
            self.operands['tables'][current_tbl_name]['is_in'] = True
            self.operands['tables'][current_tbl_name]['expression'] = {}

    def _init_old_operands(self):
        for tbl in [tbl for tbl, opt in self.operands['tables'].items() if opt['is_in'] is True]:
            if not (tbl in self.tables.keys()):
                self.operands['tables'].pop(tbl)

        for tbl, df in self.tables.items():
            exists_tbls = [tbl for tbl, opt in self.operands['tables'].items() if opt['is_in'] is True]
            if not tbl.replace(' ', '_') in exists_tbls:
                tbl_name = tbl
                for col in df.columns:
                    new_col_self_name = self.new_name(str(col).replace(' ', '_'), self.columns_id)
                    self.operands['tables'].setdefault(str(tbl).replace(' ', '_'), dict()).setdefault(
                        'fields', dict())[new_col_self_name] = {
                        'self_name': new_col_self_name,
                        'display_name': col,
                        'type': 'Поле',
                        'is_in': True,
                        'expression': {}
                    }

                self.operands['tables'][str(tbl).replace(' ', '_')]['self_name'] = str(tbl).replace(' ', '_')
                self.operands['tables'][str(tbl).replace(' ', '_')]['display_name'] = tbl_name
                self.operands['tables'][str(tbl).replace(' ', '_')]['type'] = 'Таблица'
                self.operands['tables'][str(tbl).replace(' ', '_')]['is_in'] = True
                self.operands['tables'][str(tbl).replace(' ', '_')]['expression'] = {}

    def edit_table_name(self, self_name, display_name):
        self.operands['tables'][self_name]['display_name'] = display_name
        pattern = (2, {'type': 'Таблица'})
        self.operands['tables'] = gl.dict_inner_rename_value(
            self.operands['tables'], display_name, self_name, 'display_name', pattern=pattern)
        self._save_operands(self.operands)

        result = {
            'returned_id': self_name,
            'operands': self.update_possible_values()
        }
        return result

    def edit_field_name(self, tbl_self_name, field_self_name, field_display_name):
        self.operands['tables'][tbl_self_name]['fields'][field_self_name]['display_name'] = field_display_name
        pattern = (2, {'type': 'Поле'})
        self.operands['tables'] = gl.dict_inner_rename_value(
            self.operands['tables'], field_display_name, field_self_name, 'display_name', pattern=pattern)
        self._save_operands(self.operands)
        result = {
            'returned_id': field_self_name,
            'operands': self.update_possible_values()
        }
        return result

    def add_new_table(self, tbl_name, update=True, is_new_name=True):
        _tbl_name = tbl_name.replace(' ', '_') if is_new_name else tbl_name
        if self.operands['tables'].get(_tbl_name):
            _tbl_name = self.new_name(_tbl_name, self.operands['tables']) if is_new_name else _tbl_name
        if tbl_name in [dn['display_name'] for dn in self.operands['tables'].values()]:
            tbl_name = self.new_name(tbl_name, {dn['display_name']: None for dn in self.operands['tables'].values()})
        self.operands['tables'][_tbl_name] = {
            'self_name': _tbl_name,
            'display_name': tbl_name,
            'type': 'Таблица',
            'is_in': False,
            'fields': {},
            'expression': {},
            'hidden': False if update else True
        }

        self.update_user_tables_fields_to_mapper()

        self._save_operands(self.operands)
        result = {
            'returned_id': _tbl_name,
            'operands': self.update_possible_values() if update else self.operands
        }
        return result

    def add_new_field(self, tbl_self_name, field_name, _update=True):
        _field_name = field_name.replace(' ', '_')
        _field_name = self._get_unique_column(_field_name)

        field_name = f"{self.operands['tables'][tbl_self_name]['display_name']}.{field_name}"
        if field_name in [dn['display_name'] for dn in self.operands['tables'][tbl_self_name]['fields'].values()]:
            field_name = f"{self.operands['tables'][tbl_self_name]['display_name']}.{field_name}"
            field_name = self.new_name(field_name, {
                dn['display_name']: None for dn in self.operands['tables'][tbl_self_name]['fields'].values()
            })
        self.operands['tables'][tbl_self_name]['fields'][_field_name] = {
            'self_name': _field_name,
            'display_name': field_name,
            'type': 'Поле',
            'is_in': False,
            'expression': {}
        }

        self.update_user_tables_fields_to_mapper()

        self._save_operands(self.operands)
        result = {
            'returned_id': _field_name,
            'operands': self.update_possible_values() if _update else self.operands
        }
        return result

    def edit_table_from_mapper(self, source_table_name, new_name, option=None):
        if option is None or option not in ['current_self_name', 'display_name']:
            raise AttributeError('[ADF->Prm] option is not defined')

        tbl_struct = self.operands['main_mapper'].get(source_table_name, None)
        if not tbl_struct:
            raise AttributeError('[ADF->Prm] source table name is not defined in mapper')

        result = None
        if option == 'display_name':
            self.operands['main_mapper'][tbl_struct['source_self_name']]['display_name'] = new_name
            self.edit_table_name(tbl_struct['current_self_name'], new_name)

            result = {'returned_id': source_table_name, 'operands': self.operands}
        elif option == 'current_self_name':
            new_name = new_name.replace(' ', '_')
            _tbl_to = new_name
            _tbl_from = str(tbl_struct['current_self_name'])
            old_tbl = self.operands['tables'].pop(tbl_struct['current_self_name'], None)
            if not old_tbl:
                raise AttributeError('[ADF->Prm] current table name is not defined in operands')

            whole_id = list()
            for t in self.operands['tables'].values():
                whole_id.append(t['self_name'])
                for f in t['fields'].values():
                    whole_id.append(f['self_name'])

            if new_name in whole_id:
                raise AttributeError('[ADF->Prm] Данное имя занято другим операндом')

            old_tbl['self_name'] = new_name
            self.operands['tables'][new_name] = old_tbl
            self.operands['main_mapper'][source_table_name]['current_self_name'] = new_name

            p = (2, {'type': 'Таблица'})
            p2 = {'type': 'Таблица'}

            self.operands['tables'] = \
                gl.dict_inner_rename_value(self.operands.get('tables', {}), _tbl_to, _tbl_from, 'self_name', pattern=p)
            self.operands['tables'] = \
                gl.dict_inner_rename_key(self.operands.get('tables', {}), _tbl_from, _tbl_to, inner_pattern=p2)

            result = {'returned_id': source_table_name, 'operands': self.update_possible_values()}

        self._save_operands(self.operands)

        if not result:
            raise Exception('undefined')
        return result

    def edit_field_from_mapper(self, source_table_name, source_field_name, new_name, option=None):
        if option is None or option not in ['current_self_name', 'display_name']:
            raise AttributeError('[ADF->Prm] option is not defined')

        tbl_struct = self.operands['main_mapper'].get(source_table_name, None)
        fld_struct = self.operands['main_mapper'].get(
            source_table_name, {}).get('fields', {}).get(source_field_name, None)
        if not fld_struct:
            raise AttributeError('[ADF->Prm] source field name is not defined in mapper')
        if not tbl_struct:
            raise AttributeError('[ADF->Prm] source table name is not defined in mapper')

        result = None
        if option == 'display_name':
            self.operands['main_mapper'][source_table_name]['fields'][source_field_name]['display_name'] = new_name
            self.edit_field_name(tbl_struct['current_self_name'], fld_struct['current_self_name'], new_name)

            result = {'returned_id': source_field_name, 'operands': self.operands}
        elif option == 'current_self_name':
            new_name = new_name.replace(' ', '_')
            _fld_to = new_name
            _fld_from = str(fld_struct['current_self_name'])

            old_fld = self.operands['tables'][tbl_struct['current_self_name']]['fields'].pop(
                fld_struct['current_self_name'], None)
            if not old_fld:
                raise AttributeError('[ADF->Prm] current field name is not defined in operands')

            whole_id = list()
            for t in self.operands['tables'].values():
                whole_id.append(t['self_name'])
                for f in t['fields'].values():
                    whole_id.append(f['self_name'])

            if new_name in whole_id:
                raise AttributeError('[ADF->Prm] Данное имя занято другим операндом')

            old_fld['self_name'] = new_name
            self.operands['tables'][tbl_struct['current_self_name']]['fields'][new_name] = old_fld
            self.operands['main_mapper'][source_table_name]['fields'][source_field_name]['current_self_name'] = \
                new_name

            p1 = (1, {'type': 'Поле', 'parent': _fld_from})
            p2 = (2, {'type': 'Поле'})
            p3 = {'type': 'Поле'}

            self.operands['tables'] = \
                gl.dict_inner_rename_value(self.operands.get('tables', {}), _fld_to, 'parent', pattern=p1)
            self.operands['tables'] = \
                gl.dict_inner_rename_value(self.operands.get('tables', {}), _fld_to, _fld_from, 'self_name', pattern=p2)
            self.operands['tables'] = \
                gl.dict_inner_rename_key(self.operands.get('tables', {}), _fld_from, _fld_to, inner_pattern=p3)

            result = {'returned_id': source_field_name, 'operands': self.update_possible_values()}

        self._save_operands(self.operands)

        if not result:
            raise Exception('undefined')
        return result

    def remove_table_from_mapper(self, source_table_name):
        tbl_struct = self.operands['main_mapper'].get(source_table_name, None)
        if not tbl_struct:
            raise AttributeError('[ADF->Prm] source table name is not defined in mapper')

        item = self.operands['tables'].get(tbl_struct['current_self_name'], None)
        if not item:
            raise AttributeError('[ADF->Prm] source table name is not defined in operands')

        self.operands['main_mapper'].pop(source_table_name)
        self.operands['tables'].pop(tbl_struct['current_self_name'])

        result = {'operands': self.operands}
        return result

    def remove_field_from_mapper(self, source_table_name, source_field_name):
        tbl_struct = self.operands['main_mapper'].get(source_table_name, None)
        fld_struct = self.operands['main_mapper'].get(
            source_table_name, {}).get('fields', {}).get(source_field_name, None)
        if not fld_struct:
            raise AttributeError('[ADF->Prm] source field name is not defined in mapper')

        item = self.operands['tables'].get(tbl_struct['current_self_name'], {}).get('fields', {}).get(
            fld_struct['current_self_name'], None)
        if not item:
            raise AttributeError('[ADF->Prm] source table name is not defined in operands')

        self.operands['main_mapper'][source_table_name]['fields'].pop(source_field_name)
        self.operands['tables'][tbl_struct['current_self_name']]['fields'].pop(fld_struct['current_self_name'])

        result = {'operands': self.operands}
        return result

    def remove_from_struct(self, struct, item, is_piece_of_values):
        tmp_struct = self._find_struct(struct)

        if is_piece_of_values is False or is_piece_of_values == 'False' or is_piece_of_values == 'false':
            item = eval(f"self.operands{tmp_struct}.pop(item)")
            if item['type'] == 'Функция':
                self._delete_inner_linked_functions(item)
            elif item['type'] == 'Таблица':
                for k, v in self.operands['main_mapper'].copy().items():
                    if v['current_self_name'] == item['self_name']:
                        self.operands['main_mapper'].pop(k)
                        break
            elif item['type'] == 'Поле':
                self.update_user_tables_fields_to_mapper()
        else:
            item = eval(f"self.operands{tmp_struct}['values'].pop(item)")
            if item['type'] == 'Функция':
                self._delete_inner_linked_functions(item)

        result = {
            'operands': self.update_possible_values()
        }
        return result

    def _delete_inner_linked_functions(self, item):
        if item.get('linked_by_table') is not None:
            self.operands['tables'].pop(item.get('linked_by_table'), None)
        for k, v in item['tree_struct']['Параметры'].get('Таблица_1', {}).get('values', {}).items():
            if v['type'] == 'Функция':
                self._delete_inner_linked_functions(v)
        for k, v in item['tree_struct']['Параметры'].get('Таблица_2', {}).get('values', {}).items():
            if v['type'] == 'Функция':
                self._delete_inner_linked_functions(v)
        for k, v in item['tree_struct']['Параметры'].get('Таблица', {}).get('values', {}).items():
            if v['type'] == 'Функция':
                self._delete_inner_linked_functions(v)

    def add_function_to_table(self, tbl_self_name, func_name):
        func_opts = self._get_func_opt(func_name)
        func_name = func_name.replace(' ', '_')
        if func_opts is None:
            raise ValueError(f'{func_name} does not exist')

        if 'Таблица' in func_opts['return_type']:
            func_opts['return_type'] = 'Таблица'
        else:
            raise ValueError(f'{func_name} can only return a column')

        opt_to_delete = list()
        for opt_name, opt_val in func_opts['tree_struct']['Параметры'].items():
            if 'Таблица' not in opt_val['if_return_type']:
                opt_to_delete.append(opt_name)

        for opt_del in opt_to_delete:
            func_opts['tree_struct']['Параметры'].pop(opt_del)

        self.operands['tables'][tbl_self_name]['expression'] = {
            func_name: func_opts
        }

        self._save_operands(self.operands)
        result = {
            'returned_id': func_name,
            'operands': self.update_possible_values()
        }
        return result

    def add_table_to_expression(self, struct, new_tbl_name):
        tmp_struct = self._find_struct(struct)

        res = {
            'self_name': self.operands['tables'][new_tbl_name]['self_name'],
            'display_name': self.operands['tables'][new_tbl_name]['display_name'],
            'type': 'Таблица',
            'is_in': self.operands['tables'][new_tbl_name]['is_in']
        }
        exec(f"self.operands{tmp_struct}['values'][new_tbl_name] = res")

        self._save_operands(self.operands)
        result = {
            'returned_id': res['self_name'],
            'operands': self.update_possible_values()
        }
        return result

    def add_function_to_expression(self, struct, func_name):
        func_opts = self._get_func_opt(func_name)
        if func_opts is None:
            raise ValueError(f'{func_name} does not exist')

        not_wrapped_struct = self._find_struct(struct, to_wrap=False)
        not_wrapped_struct = not_wrapped_struct.split(',')
        last_item = not_wrapped_struct[-2]
        prev_item = not_wrapped_struct[-3]

        if last_item == 'Таблица' or last_item == 'Таблица_1' or last_item == 'Таблица_2':
            if 'Таблица' in func_opts['return_type']:
                func_opts['return_type'] = 'Таблица'
                ret_type = 'Таблица'
            else:
                raise ValueError(f'{func_name} can not return a table')
        else:
            if 'Поле' in func_opts['return_type']:
                func_opts['return_type'] = 'Поле'
                ret_type = 'Поле'
            else:
                raise ValueError(f'{func_name} can not return a column')

        opt_to_delete = list()
        for opt_name, opt_val in func_opts['tree_struct']['Параметры'].items():
            if ret_type not in opt_val['if_return_type']:
                opt_to_delete.append(opt_name)

        for opt_del in opt_to_delete:
            func_opts['tree_struct']['Параметры'].pop(opt_del)

        tmp_struct = self._find_struct(struct)
        try:
            find_dct = dict()
            for tbl, tbl_opt in self.operands['tables'].items():
                if tbl_opt['expression'] != {}:
                    self._find_items(tbl_opt['expression'], 'Функция', func_name.replace(' ', '_'), find_dct)
                for fld, fld_opt in tbl_opt['fields'].items():
                    if fld_opt['expression'] != {}:
                        self._find_items(fld_opt['expression'], 'Функция', func_name.replace(' ', '_'), find_dct)
            new_func_name = self.new_name(func_name.replace(' ', '_'), find_dct)
            exec(f"self.operands{tmp_struct}['values'][new_func_name] = func_opts")
        except KeyError:
            new_func_name = func_name.replace(' ', '_')
            exec(f"self.operands{tmp_struct} = {'{}'}")
            exec(f"self.operands{tmp_struct}[new_func_name] = func_opts")

        self._save_operands(self.operands)
        result = {
            'returned_id': new_func_name,
            'operands': self.update_possible_values()
        }
        return result

    def _add_field_to_expression(self, struct, tbl_name, fld_name, is_table_expression, tree_struct__tmp_struct=None):
        tmp_struct = self._find_struct(struct)
        if tree_struct__tmp_struct is None:
            tree_struct__tmp_struct = tmp_struct[:tmp_struct.rfind('["tree_struct"]')]
        if is_table_expression == 'true':
            tbl_opt = self.operands['tables'][tbl_name]
            func_name = list(tbl_opt['expression'].keys())[0]
            if eval(f'self.operands{tree_struct__tmp_struct}["tree_struct"]["Параметры"].get("Таблица", '
                    f'{"{}"}).get("values", {"{}"})') != {}:
                tbl_prop = list(
                    eval(f'self.operands{tree_struct__tmp_struct}["tree_struct"]["Параметры"].get("Таблица", '
                         f'{"{}"}).get("values", {"{}"})').values()
                )[0]
                if tbl_prop['type'] == 'Функция':
                    tbl_name = tbl_prop['linked_by_table']
                else:
                    tbl_name = list(
                        eval(f'self.operands{tree_struct__tmp_struct}["tree_struct"]["Параметры"].get("Таблица", '
                             f'{"{}"}).get("values", {"{}"})').keys()
                    )[0]
            elif eval(f'self.operands{tree_struct__tmp_struct}["tree_struct"]["Параметры"].get("Таблица_1", '
                      f'{"{}"}).get("values", {"{}"})') != {}:
                tbl_prop = list(
                    eval(f'self.operands{tree_struct__tmp_struct}["tree_struct"]["Параметры"].get("Таблица_1", '
                         f'{"{}"}).get("values", {"{}"})').values()
                )[0]
                if tbl_prop['type'] == 'Функция':
                    tbl_name = tbl_prop['linked_by_table']
                else:
                    tbl_name = list(
                        eval(f'self.operands{tree_struct__tmp_struct}["tree_struct"]["Параметры"].get("Таблица_1", '
                             f'{"{}"}).get("values", {"{}"})').keys()
                    )[0]
                try_to_get_fld = self.operands['tables'][tbl_name]['fields'].get(fld_name)
                if try_to_get_fld is None:
                    tbl_name = None
                    if eval(f'self.operands{tree_struct__tmp_struct}["tree_struct"]["Параметры"].get("Таблица_2", '
                            f'{"{}"}).get("values", {"{}"})') != {}:
                        tbl_prop = list(
                            eval(f'self.operands{tree_struct__tmp_struct}["tree_struct"]["Параметры"].get('
                                 f'"Таблица_2", {"{}"}).get("values", {"{}"})').values()
                        )[0]
                        if tbl_prop['type'] == 'Функция':
                            tbl_name = tbl_prop['linked_by_table']
                        else:
                            tbl_name = list(
                                eval(
                                    f'self.operands{tree_struct__tmp_struct}["tree_struct"]["Параметры"].get('
                                    f'"Таблица_2", {"{}"}).get("values", {"{}"})').keys()
                            )[0]
            else:
                tree_struct__tmp_struct = tree_struct__tmp_struct[:tree_struct__tmp_struct.rfind('["tree_struct"]')]
                return self.add_field_to_expression(struct, tbl_name, fld_name, is_table_expression,
                                                    tree_struct__tmp_struct)

        if tbl_name is None:
            raise ValueError(f'Не задано имя таблицы, необходимое для выражения')

        res = {
            'self_name': self.operands['tables'][tbl_name]['fields'][fld_name]['self_name'],
            'display_name': self.operands['tables'][tbl_name]['fields'][fld_name]['display_name'],
            'type': 'Поле'
        }
        exec(f"self.operands{tmp_struct}['values'][fld_name] = res")
        return res['self_name']

    def add_field_to_expression(self, struct, tbl_name, fld_name, is_table_expression, tree_struct__tmp_struct=None):
        _id = self._add_field_to_expression(struct, tbl_name, fld_name,
                                            is_table_expression, tree_struct__tmp_struct)

        self._save_operands(self.operands)
        result = {
            'returned_id': _id,
            'operands': self.update_possible_values()
        }
        return result

    def add_fields_to_expression(self, struct, tbl_name, fld_array, is_table_expression, tree_struct__tmp_struct=None):
        returned_ids = []
        for fld_name in fld_array:
            _id = self._add_field_to_expression(struct, tbl_name, fld_name,
                                                is_table_expression, tree_struct__tmp_struct)
            returned_ids.append(_id)

        self._save_operands(self.operands)
        result = {
            'returned_id': returned_ids,
            'operands': self.update_possible_values()
        }
        return result

    def add_value_to_expression(self, struct, _obj_value):
        tmp_struct = self._find_struct(struct)

        expression_struct = self._find_struct(struct, _find_expression=True)
        find_dct = dict()
        self._find_items(eval(f"self.operands{expression_struct}"),
                         'Значение', 'НовоеЗначение', find_dct)
        new_val_name = self.new_name('НовоеЗначение', find_dct)
        val_struct = {
            'type': 'Значение',
            'self_name': new_val_name,
            'display_name': new_val_name,
            'tree_struct': {
                'value': {
                    _obj_value: {
                        'self_name': _obj_value
                    }
                }
            }
        }
        exec(f"self.operands{tmp_struct}['values'][new_val_name] = val_struct")

        self._save_operands(self.operands)
        result = {
            'returned_id': new_val_name,
            'operands': self.update_possible_values()
        }
        return result

    def _find_items(self, expression_struct, item_type, item_name_template, _find_dct):
        if not isinstance(expression_struct, dict):
            return
        for k, v in expression_struct.items():
            if not isinstance(v, dict):
                continue
            if v.get('type') == item_type and str(k).startswith(item_name_template) and k != '__possible_values__':
                _find_dct[k] = k
            self._find_items(v, item_type, item_name_template, _find_dct)

    def _find_struct(self, struct, tmp_struct='', to_wrap=True, max_iter=None, _find_expression=False, _iter=0):
        if struct == {}:
            return ''
        if max_iter is not None and max_iter == _iter:
            return tmp_struct
        for k, v in struct.items():
            if isinstance(v, dict):
                tmp_struct = f'[\"{k}\"]'
                _iter += 1
                if k == 'expression' and _find_expression is True:
                    return tmp_struct
                if to_wrap is False:
                    tmp_struct = f'{k},'

                tmp_struct += self._find_struct(v, tmp_struct, to_wrap=to_wrap, max_iter=max_iter,
                                                _find_expression=_find_expression, _iter=_iter)
        return tmp_struct

    def update_possible_values(self):
        front_operands = dict(self.operands)
        for tbl, tbl_opt in front_operands['tables'].items():
            if tbl_opt.get('hidden') is True:
                continue
            # update fields expressions
            for fld, fld_opt in tbl_opt['fields'].items():
                if fld_opt['expression'] == {}:
                    continue
                func = fld_opt['expression'][list(fld_opt['expression'].keys())[0]]
                func_ret_type = func['return_type']
                params = func['tree_struct']['Параметры']
                front_operands['tables'][tbl]['fields'][fld]['expression'][list(fld_opt['expression'].keys())[0]][
                    'tree_struct']['Параметры'] = self.update_nested_possible_values_for_fld_expression(params, tbl)

            # update tables expressions
            if tbl_opt['expression'] == {}:
                continue
            func = tbl_opt['expression'][list(tbl_opt['expression'].keys())[0]]
            func_ret_type = func['return_type']
            params = func['tree_struct']['Параметры']
            front_operands['tables'][tbl]['expression'][list(tbl_opt['expression'].keys())[0]]['tree_struct'][
                'Параметры'] = self.update_nested_possible_values_for_tbl_expression(params)

        front_operands['tables'].update(self.tried_to_calculate)
        self._save_operands(front_operands.copy())
        front_operands['tables'] = {k: v for k, v in front_operands['tables'].items() if v.get('hidden') is None or
                                    v.get('hidden') is False}
        return front_operands

    def update_nested_possible_values_for_fld_expression(self, params, tbl):
        for prm, prm_opt in params.items():
            for posb_name, posb_v in prm_opt['__possible_values__'].items():
                if posb_name == 'Поле':
                    params[prm]['__possible_values__'][posb_name] = \
                        self._get_fld_opt()[tbl]['fields'] if tbl else {}
                elif posb_name == 'Таблица':
                    params[prm]['__possible_values__'][posb_name] = self._get_tbl_opt()
                elif posb_name == 'Функция':
                    funcs_lst = list()
                    [funcs_lst.extend(list(v.keys())) for v in self.options['functions'].values()]
                    funcs = {v: {} for v in funcs_lst}
                    params[prm]['__possible_values__'][posb_name] = funcs

            for val_name, val_opt in prm_opt['values'].items():
                if val_opt['type'] == 'Функция':
                    nested_params = val_opt['tree_struct']['Параметры']
                    params[prm]['values'][val_name]['tree_struct']['Параметры'] = \
                        self.update_nested_possible_values_for_fld_expression(nested_params, tbl)

        return params

    def update_nested_possible_values_for_tbl_expression(self, params, new_tbl=None):
        new_tbl_1 = None
        new_tbl_2 = None
        if params.get('Таблица_1', None) and params.get('Таблица_2', None):
            new_tbl = None
        if params.get('Таблица', {}).get('values', {}) != {} and \
                params.get('Таблица', {}).get('values', {}) is not None:
            new_tbl = list(params['Таблица']['values'].keys())[0]
            new_tbl_prop = params['Таблица']['values'][new_tbl]
            if new_tbl_prop['type'] != 'Таблица':
                self._transform_to_datetime()
                if new_tbl_prop.get('linked_by_table'):
                    new_tbl = new_tbl_prop.get('linked_by_table')
                    new_tbl = self.update_table_from_prop(new_tbl, new_tbl_prop)
                else:
                    new_tbl = self.create_table_from_func(new_tbl, new_tbl_prop)
        elif params.get('Таблица_1', {}).get('values', {}) != {} and \
                params.get('Таблица_2', {}).get('values', {}) != {}:
            new_tbl_1 = list(params['Таблица_1']['values'].keys())[0]
            new_tbl_prop = params['Таблица_1']['values'][new_tbl_1]
            if new_tbl_prop['type'] != 'Таблица':
                self._transform_to_datetime()
                if new_tbl_prop.get('linked_by_table'):
                    new_tbl_1 = new_tbl_prop.get('linked_by_table')
                    new_tbl_1 = self.update_table_from_prop(new_tbl_1, new_tbl_prop)
                else:
                    new_tbl_1 = self.create_table_from_func(new_tbl_1, new_tbl_prop)
            new_tbl_2 = list(params['Таблица_2']['values'].keys())[0]
            new_tbl_prop = params['Таблица_2']['values'][new_tbl_2]
            if new_tbl_prop['type'] != 'Таблица':
                self._transform_to_datetime()
                if new_tbl_prop.get('linked_by_table'):
                    new_tbl_2 = new_tbl_prop.get('linked_by_table')
                    new_tbl_2 = self.update_table_from_prop(new_tbl_2, new_tbl_prop)
                else:
                    new_tbl_2 = self.create_table_from_func(new_tbl_2, new_tbl_prop)

        for prm, prm_opt in params.items():
            # if ret_type == 'Поле'
            for posb_name, posb_v in prm_opt['__possible_values__'].items():
                if posb_name == 'Поле':
                    if new_tbl is not None:
                        params[prm]['__possible_values__'][posb_name] = \
                            self._get_fld_opt()[new_tbl]['fields'] if new_tbl else {}
                    elif new_tbl_1 is not None and new_tbl_2 is not None:
                        pos_tbl_1 = self._get_fld_opt().get(new_tbl_1, {'fields': {}})['fields']
                        pos_tbl_2 = self._get_fld_opt().get(new_tbl_2, {'fields': {}})['fields']
                        posb_v_set = dict()
                        for fld, fld_opt in pos_tbl_1.items():
                            posb_v_set[fld] = fld_opt
                        for fld, fld_opt in pos_tbl_2.items():
                            posb_v_set[fld] = fld_opt
                        params[prm]['__possible_values__'][posb_name] = posb_v_set
                elif posb_name == 'Таблица':
                    params[prm]['__possible_values__'][posb_name] = self._get_tbl_opt()
                elif posb_name == 'Функция':
                    funcs_lst = list()
                    [funcs_lst.extend(list(v.keys())) for v in self.options['functions'].values()]
                    funcs = {v: {} for v in funcs_lst}
                    params[prm]['__possible_values__'][posb_name] = funcs

            for val_name, val_opt in prm_opt['values'].items():
                if val_opt['type'] == 'Функция':
                    nested_params = val_opt['tree_struct']['Параметры']
                    params[prm]['values'][val_name]['tree_struct']['Параметры'] = \
                        self.update_nested_possible_values_for_tbl_expression(nested_params, new_tbl)

        return params

    def update_table_from_prop(self, tbl_name: str, tbl_prop: dict):
        try:
            parsed_operands = self._parse_tbl_func({tbl_name: tbl_prop}, self.operands['tables'])
            self._exec_operand(tbl_name, parsed_operands, _exec_type='tables')
            self.tables[tbl_name] = self.table_df
            self.operands['tables'][tbl_name]['expression'] = {tbl_name: tbl_prop}
        except Exception:
            self.operands['tables'][tbl_name]['expression'] = {}
            self.operands['tables'][tbl_name]['fields'] = {}
            # self.operands['tables'].pop(tbl_name, None)
            return None
        return tbl_name

    def create_table_from_func(self, tbl_name: str, tbl_prop: dict):
        try:
            tbl_name = self.add_new_table(f'{tbl_name}_tbl', update=False)['returned_id']
            parsed_operands = self._parse_tbl_func({tbl_name: tbl_prop}, self.operands['tables'])
            self._exec_operand(tbl_name, parsed_operands, _exec_type='tables')
            self.tables[tbl_name] = self.table_df
            tbl_prop['linked_by_table'] = tbl_name
            self.tried_to_calculate[tbl_name] = self.operands['tables'].pop(tbl_name, None)
        except Exception:
            tbl_prop.pop('linked_by_table', None)
            self.operands['tables'].pop(tbl_name, None)
            # self.tried_to_calculate[tbl_name] = self.table_df
            return None
        return tbl_name

    def _update_fields(self):
        for tbl_name, table_df in self.tables.items():
            tbl_name = tbl_name.replace(' ', '_')
            old_fields = self.operands['tables'][tbl_name]['fields'].copy()
            self.operands['tables'][tbl_name]['fields'] = {
                k: v for k, v in self.operands['tables'][tbl_name]['fields'].items()
                if v.get('is_in') is False or k in table_df.columns
            }
            changed_columns = dict()
            for col in table_df.columns:
                if col not in list(self.operands['tables'][tbl_name]['fields'].keys()):
                    _col = self.add_new_field(tbl_name, col, _update=False)['returned_id']
                    self.operands['tables'][tbl_name]['fields'][_col]['is_in'] = True
                    # self.operands['tables'][tbl_name]['fields'][_col]['parent'] = col
                    if old_fields.get(_col):
                        self.operands['tables'][tbl_name]['fields'][_col]['display_name'] = \
                            old_fields[_col]['display_name']

                    changed_columns[col] = _col
            table_df.rename(columns=changed_columns, inplace=True)

    def refresh_data(self, _operands: dict = None, _action: str = None, ret_df=False, get_full_res=True):
        self._transform_to_datetime()

        res_data = dict()
        # self.operands = _operands  # FOR TEST MYSELF

        for k, v in self.operands['tables'].items():
            if k == _action:
                self.table_df = self.tables.get(k)
                if self.table_df is None:
                    if v['is_in'] is False:
                        self.table_df = pd.DataFrame()
                        if self.operands['tables'][k]['expression'] == {}:
                            self.operands['tables'][k]['fields'] = \
                                {k: v for k, v in self.operands['tables'][k]['fields'].items() if v['is_in'] is False}
                        else:
                            parsed_operands = self._parse_tbl_func(v['expression'], self.operands['tables'])
                            self._exec_operand(k, parsed_operands, _exec_type='tables')
                elif v['is_in'] is True:
                    self.operands['tables'][_action]['fields'] = {
                        k: v for k, v in self.operands['tables'][_action]['fields'].items()
                        if v.get('is_in') is False or k in self.table_df.columns
                    }
                    changed_columns = dict()
                    for col in self.table_df.columns:
                        if col not in list(self.operands['tables'][_action]['fields'].keys()):
                            _col = self.add_new_field(_action, col, _update=False)['returned_id']
                            self.operands['tables'][_action]['fields'][_col]['is_in'] = True
                            changed_columns[col] = _col
                    self.table_df.rename(columns=changed_columns, inplace=True)

                if isinstance(self.table_df, pd.DataFrame):
                    parsed_operands = self._parse_fields(v['fields'])
                    self._execute_operands(parsed_operands)
                    self.table_df.reset_index(inplace=True, drop=True)
                    self.table_df.replace([np.inf, -np.inf], np.nan, inplace=True)
                    self.table_df.replace({np.nan: 'NaN'}, inplace=True)
                    # for NaT expression
                    self.table_df = self.table_df.replace({np.nan: 'NaN1_DTYPE'}).replace({'NaN1_DTYPE': 'NaN'})
                    if ret_df is True:
                        return self.table_df

                    new_fld_names = {f['self_name']: f['display_name']
                                     for f in self.operands['tables'][_action]['fields'].values()}
                    self.table_df.rename(columns=new_fld_names, inplace=True)
                    self.tables['__table_df__'] = self.table_df
                    self._transform_to_datetime()
                    self._transform_from_datetime()


                    res_data = json.loads(self.table_df.to_json(orient='split'))
                    res_data.pop('index')
                    res_data['operands'] = self.update_possible_values()

                    return res_data
                else:
                    raise Exception('Таблица не идентифицирована')
        if res_data == {}:
            raise Exception('Выбранной таблицы не существует')
        return res_data

    def _parse_tbl_func(self, _struct, _tables):
        func_name = list(_struct.keys())[0]
        func_options = list(_struct.values())[0]

        params = func_options['tree_struct']['Параметры']

        _for_exec = {}
        if params.get('Таблица', None) is not None:
            named_tbl = list(params['Таблица']['values'].keys())[0]
            prop_tbl = list(params['Таблица']['values'].values())[0]
            if prop_tbl['type'] == 'Функция':
                _func_name = named_tbl
                named_tbl = prop_tbl['linked_by_table']
                _tables[named_tbl]['expression'] = {_func_name: prop_tbl}
            _for_exec = self._parse_tbl_fld_func(named_tbl, _tables, func_options)
        elif params.get('Таблица_1', None) is not None and params.get('Таблица_2', None) is not None:
            named_tbl_1 = list(params['Таблица_1']['values'].keys())[0]
            prop_tbl_1 = list(params['Таблица_1']['values'].values())[0]
            if prop_tbl_1['type'] == 'Функция':
                _func_name = named_tbl_1
                named_tbl_1 = prop_tbl_1['linked_by_table']
                _tables[named_tbl_1]['expression'] = {_func_name: prop_tbl_1}

            named_tbl_2 = list(params['Таблица_2']['values'].keys())[0]
            prop_tbl_2 = list(params['Таблица_2']['values'].values())[0]
            if prop_tbl_2['type'] == 'Функция':
                _func_name = named_tbl_2
                named_tbl_2 = prop_tbl_2['linked_by_table']
                _tables[named_tbl_2]['expression'] = {_func_name: prop_tbl_2}
            _for_exec = self._parse_tbl_tbl_func(named_tbl_1, named_tbl_2, _tables, func_options)

        return _for_exec

    def _init_tbl(self, named_tbl, _tables):

        if _tables[named_tbl]['is_in'] is True:
            self.table_df = self.tables.get(named_tbl)
            if self.table_df is None:
                raise ValueError('pd.Dataframe not found')
            parsed_operands = self._parse_fields(_tables[named_tbl]['fields'])
            self._execute_operands(parsed_operands)
            self.tables[named_tbl] = self.table_df
            self.table_df = self.table_df.copy()
        else:
            if self.tables.get(named_tbl) is not None:
                self.table_df = self.tables.get(named_tbl)
                return
            self.table_df = pd.DataFrame()
            parsed_operands = self._parse_tbl_func(_tables[named_tbl]['expression'], _tables)
            self._exec_operand(named_tbl, parsed_operands, _exec_type='tables')

            parsed_operands = self._parse_fields(_tables[named_tbl]['fields'])
            self._execute_operands(parsed_operands)

            self.tables[named_tbl] = self.table_df
            self.table_df = self.table_df.copy()

    def _parse_tbl_tbl_func(self, named_tbl_1, named_tbl_2, _tables, func_options):
        self._init_tbl(named_tbl_1, _tables)
        self._init_tbl(named_tbl_2, _tables)
        return_type = func_options['return_type']
        backend_method = func_options['backend_method']
        params = func_options['tree_struct']['Параметры']

        # options = _tables[named_tbl_1]['fields']
        parsed_params = self._parse_func_params(None, params, None)

        _for_exec = {
            'return_type': return_type,
            'backend_method': backend_method,
            'parsed_params': parsed_params
        }
        return _for_exec

    def _parse_tbl_fld_func(self, named_tbl, _tables, func_options):
        self._init_tbl(named_tbl, _tables)

        return_type = func_options['return_type']
        backend_method = func_options['backend_method']
        params = func_options['tree_struct']['Параметры']

        options = _tables[named_tbl]['fields']
        parsed_params = self._parse_func_params(None, params, options)

        _for_exec = {
            'return_type': return_type,
            'backend_method': backend_method,
            'parsed_params': parsed_params
        }
        return _for_exec

    def _parse_fields(self, options: dict):
        ret_operands = {}
        for item, struct in options.items():
            if struct['expression'] == dict():
                if not (item in self.table_df.columns):
                    # self.table_df[item] = np.nan
                    pass
            else:
                ret_operands[item] = self._parse_func(item, struct['expression'], options)
                ret_operands[item]['type'] = 'Функция'
        return ret_operands

    def _parse_func(self, parent, _struct, options):
        func_name = list(_struct.keys())[0]
        func_options = list(_struct.values())[0]

        return_type = func_options['return_type']
        backend_method = func_options['backend_method']
        params = func_options['tree_struct']['Параметры']
        if return_type == 'Таблица':
            inner_options = {}
            if params.get('Таблица'):
                if list(params['Таблица']['values'].values())[0]['type'] == 'Функция':
                    new_tbl_name = list(params['Таблица']['values'].values())[0]['linked_by_table']
                else:
                    new_tbl_name = list(params['Таблица']['values'].keys())[0]
                inner_options = self.operands['tables'][new_tbl_name]['fields']
            elif params.get('Таблица_1') and params.get('Таблица_2'):
                if list(params['Таблица_1']['values'].values())[0]['type'] == 'Функция':
                    new_tbl1_name = list(params['Таблица_1']['values'].values())[0]['linked_by_table']
                else:
                    new_tbl1_name = list(params['Таблица_1']['values'].keys())[0]
                if list(params['Таблица_2']['values'].values())[0]['type'] == 'Функция':
                    new_tbl2_name = list(params['Таблица_2']['values'].values())[0]['linked_by_table']
                else:
                    new_tbl2_name = list(params['Таблица_2']['values'].keys())[0]
                inner_options.update(self.operands['tables'][new_tbl1_name]['fields'])
                inner_options.update(self.operands['tables'][new_tbl2_name]['fields'])
            parsed_params = self._parse_func_params(parent, params, inner_options)
        else:
            parsed_params = self._parse_func_params(parent, params, options)

        _for_exec = {
            'return_type': return_type,
            'backend_method': backend_method,
            'parsed_params': parsed_params
        }
        return _for_exec

    def _parse_func_params(self, parent, _params, options):
        parsed_params = dict()
        for param, param_options in _params.items():
            parsed_params[param] = dict()
            for inp_name, inp_options in param_options['values'].items():
                parsed_params[param][inp_name] = dict()
                if inp_options['type'] == 'Поле':
                    parsed_params[param][inp_name]['type'] = 'Поле'
                    parsed_params[param][inp_name]['value'] = inp_name
                    if options:
                        if options[inp_name]['expression'] == dict() or parent == inp_name:
                            parsed_params[param][inp_name]['to_calculate'] = False
                        else:
                            parsed_params[param][inp_name]['to_calculate'] = True
                            parsed_params[param][inp_name]['tree_struct'] = self._parse_func(
                                inp_name,
                                options[inp_name]['expression'],
                                options
                            )
                    else:
                        parsed_params[param][inp_name]['to_calculate'] = False
                elif inp_options['type'] == 'Функция':
                    parsed_params[param][inp_name] = self._parse_func(parent, {inp_name: inp_options}, options)
                    parsed_params[param][inp_name]['type'] = 'Функция'
                    parsed_params[param][inp_name]['linked_by_table'] = inp_options.get('linked_by_table')
                elif inp_options['type'] == 'Таблица':
                    parsed_params[param][inp_name]['to_calculate'] = False
                    parsed_params[param][inp_name]['type'] = 'Таблица'
                    parsed_params[param][inp_name]['value'] = inp_name
                elif inp_options['type'] == 'Значение':
                    parsed_params[param][inp_name]['to_calculate'] = False
                    parsed_params[param][inp_name]['type'] = 'Значение'
                    parsed_params[param][inp_name]['value'] = list(inp_options['tree_struct']['value'].keys())[0]

        return parsed_params

    def _execute_operands(self, parsed_operands):
        for item, options in parsed_operands.items():
            _type = 'fields' if options['return_type'] == 'Поле' else 'tables'
            self._exec_operand(item, options, _exec_type=_type)

    def _exec_operand(self, param, param_options, _exec_type):
        if param in self.tmp_calculated[_exec_type]:
            return
        if param_options['backend_method'] == '_f_ra_data_selection':
            self._f_ra_data_selection(param, param_options)
            return
        for prm, prm_opt in param_options['parsed_params'].items():
            for k, v in prm_opt.items():
                if v['type'] == 'Поле':
                    if v['to_calculate'] is True:
                        self._exec_operand(k, v['tree_struct'], _exec_type='fields')
                elif v['type'] == 'Таблица':
                    if v['to_calculate'] is False:
                        pass
                elif v['type'] == 'Значение':
                    if v['to_calculate'] is False:
                        pass
                else:
                    _type = 'fields' if v['return_type'] == 'Поле' else 'tables'
                    if v.get('linked_by_table'):
                        self._exec_operand(v.get('linked_by_table'), v, _exec_type=_type)
                    else:
                        self._exec_operand(k, v, _exec_type=_type)

        # выполнить функцию
        backend_method = param_options['backend_method']
        inputs = {
            'ret_type': param_options['return_type'],
            'parsed_params': param_options['parsed_params']
        }
        res = None
        if param_options['return_type'] == 'Таблица':
            self.tables[param] = self.table_df
            self.table_df = self.table_df.copy()
        exec(f'res = self.{backend_method}(param, inputs)')
        if param_options['return_type'] == 'Таблица':
            self.tmp_calculated['tables'].append(param)
        else:
            self.tmp_calculated['fields'].append(param)
        return res

    def _f_ra_data_selection(self, param, param_options):
        if param_options['return_type'] == 'Таблица':
            self._f_ra_data_selection_tbl(param, param_options)
        elif param_options['return_type'] == 'Поле':
            self._f_ra_data_selection_fld(param, param_options)

    def _f_ra_data_selection_tbl(self, param, param_options, _is_nested=False):
        vals = param_options['parsed_params']['Таблица']
        tbl_prop = list(vals.values())[0]
        if tbl_prop['type'] == 'Функция':
            tbl_name = tbl_prop['linked_by_table']
        else:
            tbl_name = list(vals.keys())[0]
        self.table_df = self.tables.get(tbl_name)
        if self.table_df is None:
            raise KeyError('[data_selection_tbl] table_df does not exists')

        end_cols = list(param_options['parsed_params'].get('Результирующие_поля', {}).keys())
        new_param = list(param_options['parsed_params']['Функция_сравнения'].keys())
        _call_str = ':'
        if new_param:
            new_param = new_param[0]
            _call_str = self._get_call_str_from_data_selection(new_param,
                                                               param_options['parsed_params']['Функция_сравнения'][
                                                                   new_param])
        if _is_nested is True:
            return _call_str
        else:
            try:
                self.table_df = eval(f'self.table_df[{_call_str}]')

                if end_cols:
                    filter_cols = []
                    for end_col in end_cols:
                        filter_cols.extend([col for col in self.table_df.columns if col.startswith(end_col)])

                    filter_cols = list(set(filter_cols))
                    self.table_df = self.table_df[filter_cols]
                self.tables[param] = self.table_df
                self._try_to_create_new_fields_for_table(param, param_options)
            except:
                raise ValueError('undefined')

    def _get_call_str_from_data_selection(self, func_name, function_compare):
        copied_parsed_params = {'parsed_params': {}}
        for prm, prm_opt in function_compare['parsed_params'].items():
            for k, v in prm_opt.items():
                if v['type'] == 'Функция':
                    copied_parsed_params['parsed_params'][prm] = self._get_call_str_from_data_selection(k, v)
                elif v['type'] == 'Поле':
                    copied_parsed_params['parsed_params'][prm] = {
                        'type': 'Поле',
                        'value': k
                    }
                elif v['type'] == 'Значение':
                    copied_parsed_params['parsed_params'][prm] = {
                        'type': 'Значение',
                        'value': v['value']
                    }

        # выполнить функцию
        backend_method = function_compare['backend_method']
        inputs = {
            'ret_type': function_compare['return_type'],
            'parsed_params': copied_parsed_params['parsed_params']
        }
        _call_str = eval(f'self.{backend_method}(None, inputs, True)')

        return _call_str

    def _f_ra_data_selection_fld(self, param, param_options):
        pass

    def _f_ao_sum(self, param, inputs, _is_ds=False):
        if _is_ds:
            left = inputs['parsed_params']['Левый_операнд']
            if not isinstance(left, str):
                if left['type'] == 'Поле':
                    left = f'self.table_df[\'{left["value"]}\']'
                else:
                    left = left['value']

            right = inputs['parsed_params']['Правый_операнд']
            if not isinstance(right, str):
                if right['type'] == 'Поле':
                    right = f'self.table_df[\'{right["value"]}\']'
                else:
                    right = right['value']
            return f'({left}+{right})'
        else:
            left_name = list(inputs['parsed_params']['Левый_операнд'].keys())[0]
            left = {
                'type': inputs['parsed_params']['Левый_операнд'][left_name]['type'],
                'self_name': left_name,
                'value': inputs['parsed_params']['Левый_операнд'][left_name].get('value', None)
            }
            right_name = list(inputs['parsed_params']['Правый_операнд'].keys())[0]
            right = {
                'type': inputs['parsed_params']['Правый_операнд'][right_name]['type'],
                'self_name': right_name,
                'value': inputs['parsed_params']['Правый_операнд'][right_name].get('value', None)
            }

            if left['type'] in ['Поле', 'Функция'] and right['type'] in ['Поле', 'Функция']:
                if self.table_df[left['self_name']].dtype == 'datetime64[ns]' and \
                        pd.api.types.is_numeric_dtype(self.table_df[right['self_name']]):
                    _right = pd.to_timedelta(self.table_df[right['self_name']], unit='D')
                    self.table_df[param] = self.table_df[left['self_name']] + _right
                else:
                    if pd.api.types.is_numeric_dtype(self.table_df[left['self_name']]) and \
                            pd.api.types.is_numeric_dtype(self.table_df[right['self_name']]):
                        self.table_df[param] = self.table_df[left['self_name']].fillna(0) + \
                                               self.table_df[right['self_name']].fillna(0)
                    else:
                        self.table_df[param] = self.table_df[left['self_name']] + self.table_df[right['self_name']]
            elif left['type'] in ['Поле', 'Функция'] and right['type'] == 'Значение':
                if self.table_df[left['self_name']].dtype == 'datetime64[ns]' and \
                        not isinstance(fast_real(right['value']), str):
                    _right = datetime.timedelta(days=int(right['value']))
                    self.table_df[param] = self.table_df[left['self_name']] + _right
                else:
                    if pd.api.types.is_numeric_dtype(self.table_df[left['self_name']]) and \
                            not isinstance(fast_real(right['value']), str):
                        self.table_df[param] = self.table_df[left['self_name']].fillna(0) + fast_real(right['value'])
                    else:
                        self.table_df[param] = self.table_df[left['self_name']] + fast_real(right['value'])
            elif left['type'] == 'Значение' and right['type'] in ['Поле', 'Функция']:
                if not isinstance(fast_real(left['value']), str) and \
                        pd.api.types.is_numeric_dtype(self.table_df[right['self_name']]):
                    self.table_df[param] = fast_real(left['value']) + self.table_df[right['self_name']].fillna(0)
                else:
                    self.table_df[param] = fast_real(left['value']) + self.table_df[right['self_name']]
            elif left['type'] == 'Значение' and right['type'] == 'Значение':
                self.table_df[param] = fast_real(left['value']) + fast_real(right['value'])

            if self.table_df[param].dtype == 'timedelta64[ns]':
                self.table_df[param] = self.table_df[param].dt.days

            # Максимальная точность работает при 15 цифрах после запятой
            self.table_df = self.table_df.round(14)
            self._filter_runtime_fields({left_name: left, right_name: right})

    def _f_ao_abs(self, param, inputs, _is_ds=False):
        old_col = inputs['parsed_params']['Операнд']
        old_col = list(old_col.keys())[0]
        self.table_df[param] = self.table_df[old_col].abs()

        self.table_df = self.table_df.round(14)
        self._filter_runtime_fields({old_col: list(inputs['parsed_params']['Операнд'].values())[0]})

    def _f_ao_difference(self, param, inputs, _is_ds=False):
        if _is_ds:
            left = inputs['parsed_params']['Левый_операнд']
            if not isinstance(left, str):
                if left['type'] == 'Поле':
                    left = f'self.table_df[\'{left["value"]}\']'
                else:
                    left = left['value']

            right = inputs['parsed_params']['Правый_операнд']
            if not isinstance(right, str):
                if right['type'] == 'Поле':
                    right = f'self.table_df[\'{right["value"]}\']'
                else:
                    right = right['value']
            return f'({left}-{right})'
        else:
            left_name = list(inputs['parsed_params']['Левый_операнд'].keys())[0]
            left = {
                'type': inputs['parsed_params']['Левый_операнд'][left_name]['type'],
                'self_name': left_name,
                'value': inputs['parsed_params']['Левый_операнд'][left_name].get('value', None)
            }
            right_name = list(inputs['parsed_params']['Правый_операнд'].keys())[0]
            right = {
                'type': inputs['parsed_params']['Правый_операнд'][right_name]['type'],
                'self_name': right_name,
                'value': inputs['parsed_params']['Правый_операнд'][right_name].get('value', None)
            }

            if left['type'] in ['Поле', 'Функция'] and right['type'] in ['Поле', 'Функция']:
                if self.table_df[left['self_name']].dtype == 'datetime64[ns]' and \
                        pd.api.types.is_numeric_dtype(self.table_df[right['self_name']]):
                    _right = pd.to_timedelta(self.table_df[right['self_name']], unit='D')
                    self.table_df[param] = self.table_df[left['self_name']] - _right
                else:
                    if pd.api.types.is_numeric_dtype(self.table_df[left['self_name']]) and \
                            pd.api.types.is_numeric_dtype(self.table_df[right['self_name']]):
                        self.table_df[param] = self.table_df[left['self_name']].fillna(0) - \
                                               self.table_df[right['self_name']].fillna(0)
                    else:
                        self.table_df[param] = self.table_df[left['self_name']] - self.table_df[right['self_name']]
            elif left['type'] in ['Поле', 'Функция'] and right['type'] == 'Значение':
                if self.table_df[left['self_name']].dtype == 'datetime64[ns]' and \
                        not isinstance(fast_real(right['value']), str):
                    _right = datetime.timedelta(days=int(right['value']))
                    self.table_df[param] = self.table_df[left['self_name']] - _right
                else:
                    if pd.api.types.is_numeric_dtype(self.table_df[left['self_name']]) and \
                            not isinstance(fast_real(right['value']), str):
                        self.table_df[param] = self.table_df[left['self_name']].fillna(0) - fast_real(right['value'])
                    else:
                        self.table_df[param] = self.table_df[left['self_name']] - fast_real(right['value'])
            elif left['type'] == 'Значение' and right['type'] in ['Поле', 'Функция']:
                if not isinstance(fast_real(left['value']), str) and \
                        pd.api.types.is_numeric_dtype(self.table_df[right['self_name']]):
                    self.table_df[param] = fast_real(left['value']) - self.table_df[right['self_name']].fillna(0)
                else:
                    self.table_df[param] = fast_real(left['value']) - self.table_df[right['self_name']]
            elif left['type'] == 'Значение' and right['type'] == 'Значение':
                self.table_df[param] = fast_real(left['value']) - fast_real(right['value'])

            if self.table_df[param].dtype == 'timedelta64[ns]':
                self.table_df[param] = self.table_df[param].dt.days

            self.table_df = self.table_df.round(14)
            self._filter_runtime_fields({left_name: left, right_name: right})

    def _f_ao_composition(self, param, inputs, _is_ds=False):
        if _is_ds:
            left = inputs['parsed_params']['Левый_операнд']
            if not isinstance(left, str):
                if left['type'] == 'Поле':
                    left = f'self.table_df[\'{left["value"]}\']'
                else:
                    left = left['value']

            right = inputs['parsed_params']['Правый_операнд']
            if not isinstance(right, str):
                if right['type'] == 'Поле':
                    right = f'self.table_df[\'{right["value"]}\']'
                else:
                    right = right['value']
            return f'({left}*{right})'
        else:
            left_name = list(inputs['parsed_params']['Левый_операнд'].keys())[0]
            left = {
                'type': inputs['parsed_params']['Левый_операнд'][left_name]['type'],
                'self_name': left_name,
                'value': inputs['parsed_params']['Левый_операнд'][left_name].get('value', None)
            }
            right_name = list(inputs['parsed_params']['Правый_операнд'].keys())[0]
            right = {
                'type': inputs['parsed_params']['Правый_операнд'][right_name]['type'],
                'self_name': right_name,
                'value': inputs['parsed_params']['Правый_операнд'][right_name].get('value', None)
            }

            if left['type'] in ['Поле', 'Функция'] and right['type'] in ['Поле', 'Функция']:
                if pd.api.types.is_numeric_dtype(self.table_df[left['self_name']]) and \
                        pd.api.types.is_numeric_dtype(self.table_df[right['self_name']]):
                    self.table_df[param] = self.table_df[left['self_name']].fillna(0) * \
                                           self.table_df[right['self_name']].fillna(0)
                else:
                    self.table_df[param] = self.table_df[left['self_name']] * self.table_df[right['self_name']]
            elif left['type'] in ['Поле', 'Функция'] and right['type'] == 'Значение':
                if pd.api.types.is_numeric_dtype(self.table_df[left['self_name']]) and \
                        not isinstance(fast_real(right['value']), str):
                    self.table_df[param] = self.table_df[left['self_name']].fillna(0) * fast_real(right['value'])
                else:
                    self.table_df[param] = self.table_df[left['self_name']] * fast_real(right['value'])
            elif left['type'] == 'Значение' and right['type'] in ['Поле', 'Функция']:
                if not isinstance(fast_real(left['value']), str) and \
                        pd.api.types.is_numeric_dtype(self.table_df[right['self_name']]):
                    self.table_df[param] = fast_real(left['value']) * self.table_df[right['self_name']].fillna(0)
                else:
                    self.table_df[param] = fast_real(left['value']) * self.table_df[right['self_name']]
            elif left['type'] == 'Значение' and right['type'] == 'Значение':
                self.table_df[param] = fast_real(left['value']) * fast_real(right['value'])

            if self.table_df[param].dtype == 'timedelta64[ns]':
                self.table_df[param] = self.table_df[param].dt.days

            self.table_df = self.table_df.round(14)
            self._filter_runtime_fields({left_name: left, right_name: right})

    def _f_ao_quotient(self, param, inputs, _is_ds=False):
        if _is_ds:
            left = inputs['parsed_params']['Левый_операнд']
            if not isinstance(left, str):
                if left['type'] == 'Поле':
                    left = f'self.table_df[\'{left["value"]}\']'
                else:
                    left = left['value']

            right = inputs['parsed_params']['Правый_операнд']
            if not isinstance(right, str):
                if right['type'] == 'Поле':
                    right = f'self.table_df[\'{right["value"]}\']'
                else:
                    right = right['value']
            return f'({left}/{right})'
        else:
            left_name = list(inputs['parsed_params']['Левый_операнд'].keys())[0]
            left = {
                'type': inputs['parsed_params']['Левый_операнд'][left_name]['type'],
                'self_name': left_name,
                'value': inputs['parsed_params']['Левый_операнд'][left_name].get('value', None)
            }
            right_name = list(inputs['parsed_params']['Правый_операнд'].keys())[0]
            right = {
                'type': inputs['parsed_params']['Правый_операнд'][right_name]['type'],
                'self_name': right_name,
                'value': inputs['parsed_params']['Правый_операнд'][right_name].get('value', None)
            }

            if left['type'] in ['Поле', 'Функция'] and right['type'] in ['Поле', 'Функция']:
                self.table_df[param] = self.table_df[left['self_name']] / self.table_df[right['self_name']]
            elif left['type'] in ['Поле', 'Функция'] and right['type'] == 'Значение':
                self.table_df[param] = self.table_df[left['self_name']] / fast_real(right['value'])
            elif left['type'] == 'Значение' and right['type'] in ['Поле', 'Функция']:
                self.table_df[param] = fast_real(left['value']) / self.table_df[right['self_name']]
            elif left['type'] == 'Значение' and right['type'] == 'Значение':
                self.table_df[param] = fast_real(left['value']) / fast_real(right['value'])

            if self.table_df[param].dtype == 'timedelta64[ns]':
                self.table_df[param] = self.table_df[param].dt.days

            self.table_df = self.table_df.round(14)
            self._filter_runtime_fields({left_name: left, right_name: right})

    def _f_ao_partial_quotient(self, param, inputs, _is_ds=False):
        if _is_ds:
            left = inputs['parsed_params']['Левый_операнд']
            if not isinstance(left, str):
                if left['type'] == 'Поле':
                    left = f'self.table_df[\'{left["value"]}\']'
                else:
                    left = left['value']

            right = inputs['parsed_params']['Правый_операнд']
            if not isinstance(right, str):
                if right['type'] == 'Поле':
                    right = f'self.table_df[\'{right["value"]}\']'
                else:
                    right = right['value']
            return f'({left}//{right})'
        else:
            left_name = list(inputs['parsed_params']['Левый_операнд'].keys())[0]
            left = {
                'type': inputs['parsed_params']['Левый_операнд'][left_name]['type'],
                'self_name': left_name,
                'value': inputs['parsed_params']['Левый_операнд'][left_name].get('value', None)
            }
            right_name = list(inputs['parsed_params']['Правый_операнд'].keys())[0]
            right = {
                'type': inputs['parsed_params']['Правый_операнд'][right_name]['type'],
                'self_name': right_name,
                'value': inputs['parsed_params']['Правый_операнд'][right_name].get('value', None)
            }

            if left['type'] in ['Поле', 'Функция'] and right['type'] in ['Поле', 'Функция']:
                self.table_df[param] = self.table_df[left['self_name']] // self.table_df[right['self_name']]
            elif left['type'] in ['Поле', 'Функция'] and right['type'] == 'Значение':
                self.table_df[param] = self.table_df[left['self_name']] // fast_real(right['value'])
            elif left['type'] == 'Значение' and right['type'] in ['Поле', 'Функция']:
                self.table_df[param] = fast_real(left['value']) // self.table_df[right['self_name']]
            elif left['type'] == 'Значение' and right['type'] == 'Значение':
                self.table_df[param] = fast_real(left['value']) // fast_real(right['value'])

            if self.table_df[param].dtype == 'timedelta64[ns]':
                self.table_df[param] = self.table_df[param].dt.days

            self.table_df = self.table_df.round(14)
            self._filter_runtime_fields({left_name: left, right_name: right})

    def _f_ao_remainder_quotient(self, param, inputs, _is_ds=False):
        if _is_ds:
            left = inputs['parsed_params']['Левый_операнд']
            if not isinstance(left, str):
                if left['type'] == 'Поле':
                    left = f'self.table_df[\'{left["value"]}\']'
                else:
                    left = left['value']

            right = inputs['parsed_params']['Правый_операнд']
            if not isinstance(right, str):
                if right['type'] == 'Поле':
                    right = f'self.table_df[\'{right["value"]}\']'
                else:
                    right = right['value']
            return f'({left}%{right})'
        else:
            left_name = list(inputs['parsed_params']['Левый_операнд'].keys())[0]
            left = {
                'type': inputs['parsed_params']['Левый_операнд'][left_name]['type'],
                'self_name': left_name,
                'value': inputs['parsed_params']['Левый_операнд'][left_name].get('value', None)
            }
            right_name = list(inputs['parsed_params']['Правый_операнд'].keys())[0]
            right = {
                'type': inputs['parsed_params']['Правый_операнд'][right_name]['type'],
                'self_name': right_name,
                'value': inputs['parsed_params']['Правый_операнд'][right_name].get('value', None)
            }

            if left['type'] in ['Поле', 'Функция'] and right['type'] in ['Поле', 'Функция']:
                self.table_df[param] = self.table_df[left['self_name']] % self.table_df[right['self_name']]
            elif left['type'] in ['Поле', 'Функция'] and right['type'] == 'Значение':
                self.table_df[param] = self.table_df[left['self_name']] % fast_real(right['value'])
            elif left['type'] == 'Значение' and right['type'] in ['Поле', 'Функция']:
                self.table_df[param] = fast_real(left['value']) % self.table_df[right['self_name']]
            elif left['type'] == 'Значение' and right['type'] == 'Значение':
                self.table_df[param] = fast_real(left['value']) % fast_real(right['value'])

            if self.table_df[param].dtype == 'timedelta64[ns]':
                self.table_df[param] = self.table_df[param].dt.days

            self.table_df = self.table_df.round(14)
            self._filter_runtime_fields({left_name: left, right_name: right})

    def _f_ao_round(self, param, inputs):
        ret_type = inputs['ret_type']
        if ret_type == 'Поле':
            self._f_ao_round_as_field(param, inputs)
        else:
            self._f_ao_round_as_table(param, inputs)

    def _f_ao_round_as_field(self, param, inputs):
        col = inputs['parsed_params']['Измерения']
        _col = list(col.keys())[0]
        self.table_df[param] = self.table_df[_col].round().astype('int64')
        self._filter_runtime_fields({_col: col[_col]})

    def _f_ao_round_as_table(self, param, inputs):
        cols = inputs['parsed_params']['Измерения']
        cols = list(cols.keys())
        for col in cols:
            self.table_df[col] = self.table_df[col].round().astype('int64')
        self._try_to_create_new_fields_for_table(param, inputs)

    def _f_pt_int64(self, param, inputs):
        ret_type = inputs['ret_type']
        if ret_type == 'Поле':
            self._f_pt_int64_as_field(param, inputs)
        else:
            self._f_pt_int64_as_table(param, inputs)

    def _f_pt_int64_as_field(self, param, inputs):
        col = inputs['parsed_params']['Измерения']
        _col = list(col.keys())[0]
        self.table_df[param] = self.table_df[_col].astype('int64')
        self._filter_runtime_fields({_col: col[_col]})

    def _f_pt_int64_as_table(self, param, inputs):
        cols = inputs['parsed_params']['Измерения']
        cols = list(cols.keys())
        for col in cols:
            self.table_df[col] = self.table_df[col].astype('int64')
        self._try_to_create_new_fields_for_table(param, inputs)

    def _f_pt_float64(self, param, inputs):
        ret_type = inputs['ret_type']
        if ret_type == 'Поле':
            self._f_pt_float64_as_field(param, inputs)
        else:
            self._f_pt_float64_as_table(param, inputs)

    def _f_pt_float64_as_field(self, param, inputs):
        col = inputs['parsed_params']['Измерения']
        _col = list(col.keys())[0]
        self.table_df[param] = self.table_df[_col].astype('float64')
        self._filter_runtime_fields({_col: col[_col]})

    def _f_pt_float64_as_table(self, param, inputs):
        cols = inputs['parsed_params']['Измерения']
        cols = list(cols.keys())
        for col in cols:
            self.table_df[col] = self.table_df[col].astype('float64')
        self._try_to_create_new_fields_for_table(param, inputs)

    def _f_pt_datetime64(self, param, inputs):
        ret_type = inputs['ret_type']
        if ret_type == 'Поле':
            self._f_pt_datetime64_as_field(param, inputs)
        else:
            self._f_pt_datetime64_as_table(param, inputs)

    def _f_pt_datetime64_as_field(self, param, inputs):
        col = inputs['parsed_params']['Измерения']
        _col = list(col.keys())[0]
        self.table_df[param] = self.table_df[_col].astype('datetime64[ns]')
        self._filter_runtime_fields({_col: col[_col]})

    def _f_pt_datetime64_as_table(self, param, inputs):
        cols = inputs['parsed_params']['Измерения']
        cols = list(cols.keys())
        for col in cols:
            self.table_df[col] = self.table_df[col].astype('datetime64[ns]')
        self._try_to_create_new_fields_for_table(param, inputs)

    def _f_pt_str(self, param, inputs):
        ret_type = inputs['ret_type']
        if ret_type == 'Поле':
            self._f_pt_str_as_field(param, inputs)
        else:
            self._f_pt_str_as_table(param, inputs)

    def _f_pt_str_as_field(self, param, inputs):
        col = inputs['parsed_params']['Измерения']
        _col = list(col.keys())[0]
        self.table_df[param] = self.table_df[_col].astype('str')
        self._filter_runtime_fields({_col: col[_col]})

    def _f_pt_str_as_table(self, param, inputs):
        cols = inputs['parsed_params']['Измерения']
        cols = list(cols.keys())
        for col in cols:
            self.table_df[col] = self.table_df[col].astype('str')

        self._try_to_create_new_fields_for_table(param, inputs)

    def _f_os_bolshe(self, param, inputs, _is_ds=False):
        if _is_ds:
            left = inputs['parsed_params']['Левый_операнд']
            if not isinstance(left, str):
                if left['type'] == 'Поле':
                    left = f'self.table_df[\'{left["value"]}\']'
                else:
                    left = left['value']
                    if isinstance(fast_real(left), str):
                        left = '\"' + left + '\"'

            right = inputs['parsed_params']['Правый_операнд']
            if not isinstance(right, str):
                if right['type'] == 'Поле':
                    right = f'self.table_df[\'{right["value"]}\']'
                else:
                    right = right['value']
                    if isinstance(fast_real(right), str):
                        right = '\"' + right + '\"'
            return f'({left}>{right})'
        else:
            left = list(inputs['parsed_params']['Левый_операнд'].values())[0]
            left_name = list(inputs['parsed_params']['Левый_операнд'].keys())[0]
            if not isinstance(left, str):
                if left['type'] == 'Поле':
                    _left = f'self.table_df[\'{left["value"]}\']'
                elif left['type'] == 'Функция':
                    _left = f"self.table_df[\'{left_name}\']"
                else:
                    _left = left['value']

            right = list(inputs['parsed_params']['Правый_операнд'].values())[0]
            right_name = list(inputs['parsed_params']['Правый_операнд'].keys())[0]
            if not isinstance(right, str):
                if right['type'] == 'Поле':
                    _right = f'self.table_df[\'{right["value"]}\']'
                elif right['type'] == 'Функция':
                    _right = f"self.table_df[\'{right_name}\']"
                else:
                    _right = right['value']

            try:
                if_true = list(inputs['parsed_params']['Если_верно'].values())[0]
                if_true_name = list(inputs['parsed_params']['Если_верно'].keys())[0]
            except IndexError:
                _if_true = 1
            else:
                if not isinstance(if_true, str):
                    if if_true['type'] == 'Поле':
                        _if_true = f'self.table_df[\'{if_true["value"]}\']'
                    elif if_true['type'] == 'Функция':
                        _if_true = f"self.table_df[\'{if_true_name}\']"
                    else:
                        _if_true = if_true['value']

            try:
                if_false = list(inputs['parsed_params']['Если_ложно'].values())[0]
                if_false_name = list(inputs['parsed_params']['Если_ложно'].keys())[0]
            except IndexError:
                _if_false = 0
            else:
                if not isinstance(if_false, str):
                    if if_false['type'] == 'Поле':
                        _if_false = f'self.table_df[\'{if_false["value"]}\']'
                    elif if_false['type'] == 'Функция':
                        _if_false = f"self.table_df[\'{if_false_name}\']"
                    else:
                        _if_false = if_false['value']

            self.table_df[param] = eval(f'np.where({_left}>{_right}, {_if_true}, {_if_false})')

            check_dct = {left_name: left, right_name: right}
            for param in ['if_true', 'if_false']:
                if param in locals():
                    exec(f"check_dct[{param + '_name'}] = {param}")
            self._filter_runtime_fields(check_dct)

    def _f_os_bolshe_libo_ravno(self, param, inputs, _is_ds=False):
        if _is_ds:
            left = inputs['parsed_params']['Левый_операнд']
            if not isinstance(left, str):
                if left['type'] == 'Поле':
                    left = f'self.table_df[\'{left["value"]}\']'
                else:
                    left = left['value']
                    if isinstance(fast_real(left), str):
                        left = '\"' + left + '\"'

            right = inputs['parsed_params']['Правый_операнд']
            if not isinstance(right, str):
                if right['type'] == 'Поле':
                    right = f'self.table_df[\'{right["value"]}\']'
                else:
                    right = right['value']
                    if isinstance(fast_real(right), str):
                        right = '\"' + right + '\"'
            return f'({left}>={right})'
        else:
            left = list(inputs['parsed_params']['Левый_операнд'].values())[0]
            left_name = list(inputs['parsed_params']['Левый_операнд'].keys())[0]
            if not isinstance(left, str):
                if left['type'] == 'Поле':
                    _left = f'self.table_df[\'{left["value"]}\']'
                elif left['type'] == 'Функция':
                    _left = f"self.table_df[\'{left_name}\']"
                else:
                    _left = left['value']

            right = list(inputs['parsed_params']['Правый_операнд'].values())[0]
            right_name = list(inputs['parsed_params']['Правый_операнд'].keys())[0]
            if not isinstance(right, str):
                if right['type'] == 'Поле':
                    _right = f'self.table_df[\'{right["value"]}\']'
                elif right['type'] == 'Функция':
                    _right = f"self.table_df[\'{right_name}\']"
                else:
                    _right = right['value']

            try:
                if_true = list(inputs['parsed_params']['Если_верно'].values())[0]
                if_true_name = list(inputs['parsed_params']['Если_верно'].keys())[0]
            except IndexError:
                _if_true = 1
            else:
                if not isinstance(if_true, str):
                    if if_true['type'] == 'Поле':
                        _if_true = f'self.table_df[\'{if_true["value"]}\']'
                    elif if_true['type'] == 'Функция':
                        _if_true = f"self.table_df[\'{if_true_name}\']"
                    else:
                        _if_true = if_true['value']

            try:
                if_false = list(inputs['parsed_params']['Если_ложно'].values())[0]
                if_false_name = list(inputs['parsed_params']['Если_ложно'].keys())[0]
            except IndexError:
                _if_false = 0
            else:
                if not isinstance(if_false, str):
                    if if_false['type'] == 'Поле':
                        _if_false = f'self.table_df[\'{if_false["value"]}\']'
                    elif if_false['type'] == 'Функция':
                        _if_false = f"self.table_df[\'{if_false_name}\']"
                    else:
                        _if_false = if_false['value']

            self.table_df[param] = eval(f'np.where({_left}>={_right}, {_if_true}, {_if_false})')

            check_dct = {left_name: left, right_name: right}
            for param in ['if_true', 'if_false']:
                if param in locals():
                    exec(f"check_dct[{param + '_name'}] = {param}")
            self._filter_runtime_fields(check_dct)

    def _f_os_menshe(self, param, inputs, _is_ds=False):
        if _is_ds:
            left = inputs['parsed_params']['Левый_операнд']
            if not isinstance(left, str):
                if left['type'] == 'Поле':
                    left = f'self.table_df[\'{left["value"]}\']'
                else:
                    left = left['value']
                    if isinstance(fast_real(left), str):
                        left = '\"' + left + '\"'

            right = inputs['parsed_params']['Правый_операнд']
            if not isinstance(right, str):
                if right['type'] == 'Поле':
                    right = f'self.table_df[\'{right["value"]}\']'
                else:
                    right = right['value']
                    if isinstance(fast_real(right), str):
                        right = '\"' + right + '\"'
            return f'({left}<{right})'
        else:
            left = list(inputs['parsed_params']['Левый_операнд'].values())[0]
            left_name = list(inputs['parsed_params']['Левый_операнд'].keys())[0]
            if not isinstance(left, str):
                if left['type'] == 'Поле':
                    _left = f'self.table_df[\'{left["value"]}\']'
                elif left['type'] == 'Функция':
                    _left = f"self.table_df[\'{left_name}\']"
                else:
                    _left = left['value']

            right = list(inputs['parsed_params']['Правый_операнд'].values())[0]
            right_name = list(inputs['parsed_params']['Правый_операнд'].keys())[0]
            if not isinstance(right, str):
                if right['type'] == 'Поле':
                    _right = f'self.table_df[\'{right["value"]}\']'
                elif right['type'] == 'Функция':
                    _right = f"self.table_df[\'{right_name}\']"
                else:
                    _right = right['value']

            try:
                if_true = list(inputs['parsed_params']['Если_верно'].values())[0]
                if_true_name = list(inputs['parsed_params']['Если_верно'].keys())[0]
            except IndexError:
                _if_true = 1
            else:
                if not isinstance(if_true, str):
                    if if_true['type'] == 'Поле':
                        _if_true = f'self.table_df[\'{if_true["value"]}\']'
                    elif if_true['type'] == 'Функция':
                        _if_true = f"self.table_df[\'{if_true_name}\']"
                    else:
                        _if_true = if_true['value']

            try:
                if_false = list(inputs['parsed_params']['Если_ложно'].values())[0]
                if_false_name = list(inputs['parsed_params']['Если_ложно'].keys())[0]
            except IndexError:
                _if_false = 0
            else:
                if not isinstance(if_false, str):
                    if if_false['type'] == 'Поле':
                        _if_false = f'self.table_df[\'{if_false["value"]}\']'
                    elif if_false['type'] == 'Функция':
                        _if_false = f"self.table_df[\'{if_false_name}\']"
                    else:
                        _if_false = if_false['value']

            self.table_df[param] = eval(f'np.where({_left}<{_right}, {_if_true}, {_if_false})')

            check_dct = {left_name: left, right_name: right}
            for param in ['if_true', 'if_false']:
                if param in locals():
                    exec(f"check_dct[{param + '_name'}] = {param}")
            self._filter_runtime_fields(check_dct)

    def _f_os_menshe_libo_ravno(self, param, inputs, _is_ds=False):
        if _is_ds:
            left = inputs['parsed_params']['Левый_операнд']
            if not isinstance(left, str):
                if left['type'] == 'Поле':
                    left = f'self.table_df[\'{left["value"]}\']'
                else:
                    left = left['value']
                    if isinstance(fast_real(left), str):
                        left = '\"' + left + '\"'

            right = inputs['parsed_params']['Правый_операнд']
            if not isinstance(right, str):
                if right['type'] == 'Поле':
                    right = f'self.table_df[\'{right["value"]}\']'
                else:
                    right = right['value']
                    if isinstance(fast_real(right), str):
                        right = '\"' + right + '\"'
            return f'({left}<={right})'
        else:
            left = list(inputs['parsed_params']['Левый_операнд'].values())[0]
            left_name = list(inputs['parsed_params']['Левый_операнд'].keys())[0]
            if not isinstance(left, str):
                if left['type'] == 'Поле':
                    _left = f'self.table_df[\'{left["value"]}\']'
                elif left['type'] == 'Функция':
                    _left = f"self.table_df[\'{left_name}\']"
                else:
                    _left = left['value']

            right = list(inputs['parsed_params']['Правый_операнд'].values())[0]
            right_name = list(inputs['parsed_params']['Правый_операнд'].keys())[0]
            if not isinstance(right, str):
                if right['type'] == 'Поле':
                    _right = f'self.table_df[\'{right["value"]}\']'
                elif right['type'] == 'Функция':
                    _right = f"self.table_df[\'{right_name}\']"
                else:
                    _right = right['value']

            try:
                if_true = list(inputs['parsed_params']['Если_верно'].values())[0]
                if_true_name = list(inputs['parsed_params']['Если_верно'].keys())[0]
            except IndexError:
                _if_true = 1
            else:
                if not isinstance(if_true, str):
                    if if_true['type'] == 'Поле':
                        _if_true = f'self.table_df[\'{if_true["value"]}\']'
                    elif if_true['type'] == 'Функция':
                        _if_true = f"self.table_df[\'{if_true_name}\']"
                    else:
                        _if_true = if_true['value']

            try:
                if_false = list(inputs['parsed_params']['Если_ложно'].values())[0]
                if_false_name = list(inputs['parsed_params']['Если_ложно'].keys())[0]
            except IndexError:
                _if_false = 0
            else:
                if not isinstance(if_false, str):
                    if if_false['type'] == 'Поле':
                        _if_false = f'self.table_df[\'{if_false["value"]}\']'
                    elif if_false['type'] == 'Функция':
                        _if_false = f"self.table_df[\'{if_false_name}\']"
                    else:
                        _if_false = if_false['value']

            self.table_df[param] = eval(f'np.where({_left}<={_right}, {_if_true}, {_if_false})')

            check_dct = {left_name: left, right_name: right}
            for param in ['if_true', 'if_false']:
                if param in locals():
                    exec(f"check_dct[{param + '_name'}] = {param}")
            self._filter_runtime_fields(check_dct)

    def _f_os_ravno(self, param, inputs, _is_ds=False):
        if _is_ds:
            left = inputs['parsed_params']['Левый_операнд']
            if not isinstance(left, str):
                if left['type'] == 'Поле':
                    left = f'self.table_df[\'{left["value"]}\']'
                else:
                    left = left['value']
                    if isinstance(fast_real(left), str):
                        left = '\"' + left + '\"'

            right = inputs['parsed_params']['Правый_операнд']
            if not isinstance(right, str):
                if right['type'] == 'Поле':
                    right = f'self.table_df[\'{right["value"]}\']'
                else:
                    right = right['value']
                    if isinstance(fast_real(right), str):
                        right = '\"' + right + '\"'

            if left == 'np.nan' or right == 'np.nan':
                if left == 'np.nan':
                    return f'{right}.isnull()'
                else:
                    return f'{left}.isnull()'
            else:
                return f'({left}=={right})'
        else:
            nan_expression = False

            left = list(inputs['parsed_params']['Левый_операнд'].values())[0]
            left_name = list(inputs['parsed_params']['Левый_операнд'].keys())[0]
            if not isinstance(left, str):
                if left['type'] == 'Поле':
                    _left = f'self.table_df[\'{left["value"]}\']'
                elif left['type'] == 'Функция':
                    if left['backend_method'] == '_f_pr_nan':
                        _left = np.nan
                    else:
                        _left = f"self.table_df[\'{left_name}\']"
                else:
                    _left = left['value']

            right = list(inputs['parsed_params']['Правый_операнд'].values())[0]
            right_name = list(inputs['parsed_params']['Правый_операнд'].keys())[0]
            if not isinstance(right, str):
                if right['type'] == 'Поле':
                    _right = f'self.table_df[\'{right["value"]}\']'
                elif right['type'] == 'Функция':
                    if right['backend_method'] == '_f_pr_nan':
                        _right = np.nan
                    else:
                        _right = f"self.table_df[\'{right_name}\']"
                else:
                    _right = right['value']

            try:
                if_true = list(inputs['parsed_params']['Если_верно'].values())[0]
                if_true_name = list(inputs['parsed_params']['Если_верно'].keys())[0]
            except IndexError:
                _if_true = 1
            else:
                if not isinstance(if_true, str):
                    if if_true['type'] == 'Поле':
                        _if_true = f'self.table_df[\'{if_true["value"]}\']'
                    elif if_true['type'] == 'Функция':
                        if if_true['backend_method'] == '_f_pr_nan':
                            _if_true = 'np.nan'
                        else:
                            _if_true = f"self.table_df[\'{if_true_name}\']"
                    else:
                        _if_true = if_true['value']

            try:
                if_false = list(inputs['parsed_params']['Если_ложно'].values())[0]
                if_false_name = list(inputs['parsed_params']['Если_ложно'].keys())[0]
            except IndexError:
                _if_false = 0
            else:
                if not isinstance(if_false, str):
                    if if_false['type'] == 'Поле':
                        _if_false = f'self.table_df[\'{if_false["value"]}\']'
                    elif if_false['type'] == 'Функция':
                        if if_false['backend_method'] == '_f_pr_nan':
                            _if_false = 'np.nan'
                        else:
                            _if_false = f"self.table_df[\'{if_false_name}\']"
                    else:
                        _if_false = if_false['value']

            if isinstance(_left, float):
                if np.isnan(_left):
                    nan_expression = f'{_right}.isnull()'
            if isinstance(_right, float):
                if np.isnan(_right):
                    nan_expression = f'{_left}.isnull()'

            if nan_expression is False:
                self.table_df[param] = eval(f'np.where({_left}=={_right}, {_if_true}, {_if_false})')
            else:
                self.table_df[param] = eval(f'np.where({nan_expression}, {_if_true}, {_if_false})')

            check_dct = {left_name: left, right_name: right}
            for param in ['if_true', 'if_false']:
                if param in locals():
                    exec(f"check_dct[{param + '_name'}] = {param}")
            self._filter_runtime_fields(check_dct)

    def _f_os_ne_ravno(self, param, inputs, _is_ds=False):
        if _is_ds:
            left = inputs['parsed_params']['Левый_операнд']
            if not isinstance(left, str):
                if left['type'] == 'Поле':
                    left = f'self.table_df[\'{left["value"]}\']'
                else:
                    left = left['value']
                    if isinstance(fast_real(left), str):
                        left = '\"' + left + '\"'

            right = inputs['parsed_params']['Правый_операнд']
            if not isinstance(right, str):
                if right['type'] == 'Поле':
                    right = f'self.table_df[\'{right["value"]}\']'
                else:
                    right = right['value']
                    if isinstance(fast_real(right), str):
                        right = '\"' + right + '\"'
            if left == 'np.nan' or right == 'np.nan':
                if left == 'np.nan':
                    return f'{right}.notna()'
                else:
                    return f'{left}.notna()'
            else:
                return f'({left}!={right})'
        else:
            nan_expression = False

            left = list(inputs['parsed_params']['Левый_операнд'].values())[0]
            left_name = list(inputs['parsed_params']['Левый_операнд'].keys())[0]
            if not isinstance(left, str):
                if left['type'] == 'Поле':
                    _left = f'self.table_df[\'{left["value"]}\']'
                elif left['type'] == 'Функция':
                    if left['backend_method'] == '_f_pr_nan':
                        _left = np.nan
                    else:
                        _left = f"self.table_df[\'{left_name}\']"
                else:
                    _left = left['value']

            right = list(inputs['parsed_params']['Правый_операнд'].values())[0]
            right_name = list(inputs['parsed_params']['Правый_операнд'].keys())[0]
            if not isinstance(right, str):
                if right['type'] == 'Поле':
                    _right = f'self.table_df[\'{right["value"]}\']'
                elif right['type'] == 'Функция':
                    if right['backend_method'] == '_f_pr_nan':
                        _right = np.nan
                    else:
                        _right = f"self.table_df[\'{right_name}\']"
                else:
                    _right = right['value']

            try:
                if_true = list(inputs['parsed_params']['Если_верно'].values())[0]
                if_true_name = list(inputs['parsed_params']['Если_верно'].keys())[0]
            except IndexError:
                _if_true = 1
            else:
                if not isinstance(if_true, str):
                    if if_true['type'] == 'Поле':
                        _if_true = f'self.table_df[\'{if_true["value"]}\']'
                    elif if_true['type'] == 'Функция':
                        if if_true['backend_method'] == '_f_pr_nan':
                            _if_true = 'np.nan'
                        else:
                            _if_true = f"self.table_df[\'{if_true_name}\']"
                    else:
                        _if_true = if_true['value']

            try:
                if_false = list(inputs['parsed_params']['Если_ложно'].values())[0]
                if_false_name = list(inputs['parsed_params']['Если_ложно'].keys())[0]
            except IndexError:
                _if_false = 0
            else:
                if not isinstance(if_false, str):
                    if if_false['type'] == 'Поле':
                        _if_false = f'self.table_df[\'{if_false["value"]}\']'
                    elif if_false['type'] == 'Функция':
                        if if_false['backend_method'] == '_f_pr_nan':
                            _if_false = 'np.nan'
                        else:
                            _if_false = f"self.table_df[\'{if_false_name}\']"
                    else:
                        _if_false = if_false['value']

            if isinstance(_left, float):
                if np.isnan(_left):
                    nan_expression = f'{_right}.notna()'
            if isinstance(_right, float):
                if np.isnan(_right):
                    nan_expression = f'{_left}.notna()'

            if nan_expression is False:
                self.table_df[param] = eval(f'np.where({_left}!={_right}, {_if_true}, {_if_false})')
            else:
                self.table_df[param] = eval(f'np.where({nan_expression}, {_if_true}, {_if_false})')

            check_dct = {left_name: left, right_name: right}
            for param in ['if_true', 'if_false']:
                if param in locals():
                    exec(f"check_dct[{param + '_name'}] = {param}")
            self._filter_runtime_fields(check_dct)

    def _f_os_between(self, param, inputs, _is_ds=False):
        if _is_ds:
            operand = inputs['parsed_params']['Операнд']
            operand = f'self.table_df[\'{operand["value"]}\']'

            left = inputs['parsed_params']['Начало']
            if not isinstance(left, str):
                if left['type'] == 'Поле':
                    left = f'self.table_df[\'{left["value"]}\']'
                else:
                    left = left['value']
                    if isinstance(fast_real(left), str):
                        left = '\"' + left + '\"'

            right = inputs['parsed_params']['Конец']
            if not isinstance(right, str):
                if right['type'] == 'Поле':
                    right = f'self.table_df[\'{right["value"]}\']'
                else:
                    right = right['value']
                    if isinstance(fast_real(right), str):
                        right = '\"' + right + '\"'
            return f'({operand}.between({left}, {right}))'
        else:
            operand = list(inputs['parsed_params']['Операнд'].values())[0]
            operand_name = list(inputs['parsed_params']['Операнд'].keys())[0]
            if not isinstance(operand, str):
                if operand['type'] == 'Поле':
                    _operand = f'self.table_df[\'{operand["value"]}\']'
                elif operand['type'] == 'Функция':
                    _operand = f"self.table_df[\'{operand_name}\']"
                else:
                    _operand = operand['value']

            left = list(inputs['parsed_params']['Начало'].values())[0]
            left_name = list(inputs['parsed_params']['Начало'].keys())[0]
            if not isinstance(left, str):
                if left['type'] == 'Поле':
                    _left = f'self.table_df[\'{left["value"]}\']'
                elif left['type'] == 'Функция':
                    if left['backend_method'] == '_f_pr_nan':
                        # _left = np.nan
                        raise Exception('Функция "Промежуток" не может содержать значение NaN')
                    else:
                        _left = f"self.table_df[\'{left_name}\']"
                else:
                    _left = left['value']

            right = list(inputs['parsed_params']['Конец'].values())[0]
            right_name = list(inputs['parsed_params']['Конец'].keys())[0]
            if not isinstance(right, str):
                if right['type'] == 'Поле':
                    _right = f'self.table_df[\'{right["value"]}\']'
                elif right['type'] == 'Функция':
                    if right['backend_method'] == '_f_pr_nan':
                        # _right = np.nan
                        raise Exception('Функция "Промежуток" не может содержать значение NaN')
                    else:
                        _right = f"self.table_df[\'{right_name}\']"
                else:
                    _right = right['value']

            try:
                if_true = list(inputs['parsed_params']['Если_верно'].values())[0]
                if_true_name = list(inputs['parsed_params']['Если_верно'].keys())[0]
            except IndexError:
                _if_true = 1
            else:
                if not isinstance(if_true, str):
                    if if_true['type'] == 'Поле':
                        _if_true = f'self.table_df[\'{if_true["value"]}\']'
                    elif if_true['type'] == 'Функция':
                        if if_true['backend_method'] == '_f_pr_nan':
                            _if_true = 'np.nan'
                        else:
                            _if_true = f"self.table_df[\'{if_true_name}\']"
                    else:
                        _if_true = if_true['value']

            try:
                if_false = list(inputs['parsed_params']['Если_ложно'].values())[0]
                if_false_name = list(inputs['parsed_params']['Если_ложно'].keys())[0]
            except IndexError:
                _if_false = 0
            else:
                if not isinstance(if_false, str):
                    if if_false['type'] == 'Поле':
                        _if_false = f'self.table_df[\'{if_false["value"]}\']'
                    elif if_false['type'] == 'Функция':
                        if if_false['backend_method'] == '_f_pr_nan':
                            _if_false = 'np.nan'
                        else:
                            _if_false = f"self.table_df[\'{if_false_name}\']"
                    else:
                        _if_false = if_false['value']

            if isinstance(_left, float):
                if np.isnan(_left):
                    nan_expression = f'{_right}.notna()'
            if isinstance(_right, float):
                if np.isnan(_right):
                    nan_expression = f'{_left}.notna()'

            self.table_df[param] = eval(f'np.where({_operand}.between({_left}, {_right}), {_if_true}, {_if_false})')

            check_dct = {left_name: left, right_name: right, operand_name: operand}
            for param in ['if_true', 'if_false']:
                if param in locals():
                    exec(f"check_dct[{param + '_name'}] = {param}")
            self._filter_runtime_fields(check_dct)

    def _f_lo_and(self, param, inputs, _is_ds=False):
        if _is_ds:
            left = inputs['parsed_params']['Левый_операнд']
            if not isinstance(left, str):
                if left['type'] == 'Поле':
                    left = f'self.table_df[\'{left["value"]}\']'
                else:
                    left = left['value']

            right = inputs['parsed_params']['Правый_операнд']
            if not isinstance(right, str):
                if right['type'] == 'Поле':
                    right = f'self.table_df[\'{right["value"]}\']'
                else:
                    right = right['value']
            return f'({left}&{right})'
        else:
            pass

    def _f_lo_or(self, param, inputs, _is_ds=False):
        if _is_ds:
            left = inputs['parsed_params']['Левый_операнд']
            if not isinstance(left, str):
                if left['type'] == 'Поле':
                    left = f'self.table_df[\'{left["value"]}\']'
                else:
                    left = left['value']

            right = inputs['parsed_params']['Правый_операнд']
            if not isinstance(right, str):
                if right['type'] == 'Поле':
                    right = f'self.table_df[\'{right["value"]}\']'
                else:
                    right = right['value']
            return f'({left}|{right})'
        else:
            pass

    def _f_ra_sort_increase(self, param, inputs):
        if inputs['ret_type'] == 'Поле':
            self._f_ra_sort_increase_as_field(param, inputs)
        else:
            self._f_ra_sort_increase_as_table(param, inputs)

    def _f_ra_sort_increase_as_table(self, param, inputs):
        cols = list(inputs['parsed_params']['Измерения'].keys())
        self.table_df = self.table_df.sort_values(by=cols, ascending=True, ignore_index=True)
        self._try_to_create_new_fields_for_table(param, inputs)

    def _f_ra_sort_increase_as_field(self, param, inputs):
        col = list(inputs['parsed_params']['Измерения'].keys())[0]
        self.table_df = self.table_df.sort_values(by=col, ascending=True, ignore_index=True)
        self._filter_runtime_fields({col: list(inputs['parsed_params']['Измерения'].values())[0]})

    def _f_ra_sort_decrease(self, param, inputs):
        if inputs['ret_type'] == 'Поле':
            self._f_ra_sort_decrease_as_field(param, inputs)
        else:
            self._f_ra_sort_decrease_as_table(param, inputs)

    def _f_ra_sort_decrease_as_table(self, param, inputs):
        cols = list(inputs['parsed_params']['Измерения'].keys())
        self.table_df = self.table_df.sort_values(by=cols, ascending=False, ignore_index=True)
        self._try_to_create_new_fields_for_table(param, inputs)

    def _f_ra_sort_decrease_as_field(self, param, inputs):
        col = list(inputs['parsed_params']['Измерения'].keys())[0]
        self.table_df = self.table_df.sort_values(by=col, ascending=False, ignore_index=True)
        self._filter_runtime_fields({col: list(inputs['parsed_params']['Измерения'].values())[0]})

    def _f_ra_union(self, param, inputs):
        try:
            if list(inputs['parsed_params']['Таблица_1'].values())[0]['type'] == 'Функция':
                tbl_name_1 = list(inputs['parsed_params']['Таблица_1'].values())[0]['linked_by_table']
            else:
                tbl_name_1 = list(inputs['parsed_params']['Таблица_1'].keys())[0]
            if list(inputs['parsed_params']['Таблица_2'].values())[0]['type'] == 'Функция':
                tbl_name_2 = list(inputs['parsed_params']['Таблица_2'].values())[0]['linked_by_table']
            else:
                tbl_name_2 = list(inputs['parsed_params']['Таблица_2'].keys())[0]
            namespace_on_left = list(inputs['parsed_params']['Объединить_по_столбцу_слева'].keys())
            namespace_on_right = list(inputs['parsed_params']['Объединить_по_столбцу_справа'].keys())
            end_cols = list(inputs['parsed_params'].get('Результирующие_поля', {}).keys())
        except KeyError:
            raise KeyError('Указаны не все параметры')
        df1 = self.tables.get(tbl_name_1)
        df2 = self.tables.get(tbl_name_2)
        if df1 is not None and df2 is not None:
            if namespace_on_left and namespace_on_right and (len(namespace_on_left) == len(namespace_on_right)):
                new_fld_names = dict(zip(namespace_on_left, namespace_on_right))
                df1.rename(columns=new_fld_names, inplace=True)
            self.table_df = pd.concat([df1, df2], ignore_index=True)
        else:
            raise ValueError('undefined')

        if end_cols:
            filter_cols = []
            for end_col in end_cols:
                if end_col in self.table_df.columns:
                    filter_cols.append(end_col)

            filter_cols = list(filter_cols)
            self.table_df = self.table_df[filter_cols]

        self.tables[param] = self.table_df
        self._try_to_create_new_fields_for_table(param, inputs)

    def _f_ra_concatenation_outer(self, param, inputs):
        try:
            if list(inputs['parsed_params']['Таблица_1'].values())[0]['type'] == 'Функция':
                tbl_name_1 = list(inputs['parsed_params']['Таблица_1'].values())[0]['linked_by_table']
            else:
                tbl_name_1 = list(inputs['parsed_params']['Таблица_1'].keys())[0]
            if list(inputs['parsed_params']['Таблица_2'].values())[0]['type'] == 'Функция':
                tbl_name_2 = list(inputs['parsed_params']['Таблица_2'].values())[0]['linked_by_table']
            else:
                tbl_name_2 = list(inputs['parsed_params']['Таблица_2'].keys())[0]
            merge_on_left = list(inputs['parsed_params']['Объединить_по_столбцу_слева'].keys())
            merge_on_right = list(inputs['parsed_params']['Объединить_по_столбцу_справа'].keys())
            end_cols = list(inputs['parsed_params'].get('Результирующие_поля', {}).keys())
        except KeyError:
            raise KeyError('Указаны не все параметры')
        df1 = self.tables.get(tbl_name_1)
        df2 = self.tables.get(tbl_name_2)
        if df1 is not None and df2 is not None:
            if not merge_on_left or not merge_on_right:
                self.table_df = df1.merge(df2, how='cross', suffixes=['T1', 'T2'])
            else:
                self.table_df = df1.merge(df2, left_on=merge_on_left, right_on=merge_on_right,
                                          how='outer', suffixes=['T1', 'T2'])
        else:
            raise ValueError('undefined')

        if end_cols:
            filter_cols = []
            for end_col in end_cols:
                if end_col in self.table_df.columns:
                    filter_cols.append(end_col)
                elif (end_col + 'Т1' in self.table_df.columns and end_col + 'Т2' in self.table_df.columns) or \
                        (end_col + 'T1' in self.table_df.columns and end_col + 'T2' in self.table_df.columns):
                    filter_cols.append(end_col + 'T1')
                    filter_cols.append(end_col + 'T2')

            filter_cols = list(filter_cols)
            self.table_df = self.table_df[filter_cols]

        self.tables[param] = self.table_df
        self._try_to_create_new_fields_for_table(param, inputs)

    def _f_ra_concatenation_right(self, param, inputs):
        try:
            if list(inputs['parsed_params']['Таблица_1'].values())[0]['type'] == 'Функция':
                tbl_name_1 = list(inputs['parsed_params']['Таблица_1'].values())[0]['linked_by_table']
            else:
                tbl_name_1 = list(inputs['parsed_params']['Таблица_1'].keys())[0]
            if list(inputs['parsed_params']['Таблица_2'].values())[0]['type'] == 'Функция':
                tbl_name_2 = list(inputs['parsed_params']['Таблица_2'].values())[0]['linked_by_table']
            else:
                tbl_name_2 = list(inputs['parsed_params']['Таблица_2'].keys())[0]
            merge_on_left = list(inputs['parsed_params']['Объединить_по_столбцу_слева'].keys())
            merge_on_right = list(inputs['parsed_params']['Объединить_по_столбцу_справа'].keys())
            end_cols = list(inputs['parsed_params'].get('Результирующие_поля', {}).keys())
        except KeyError:
            raise KeyError('Указаны не все параметры')
        df1 = self.tables.get(tbl_name_1)
        df2 = self.tables.get(tbl_name_2)
        if df1 is not None and df2 is not None:
            if not merge_on_left or not merge_on_right:
                self.table_df = df1.merge(df2, how='cross', suffixes=['T1', 'T2'])
            else:
                self.table_df = df1.merge(df2, left_on=merge_on_left, right_on=merge_on_right,
                                          how='right', suffixes=['T1', 'T2'])
        else:
            raise ValueError('undefined')

        if end_cols:
            filter_cols = []
            for end_col in end_cols:
                if end_col in self.table_df.columns:
                    filter_cols.append(end_col)
                elif (end_col + 'Т1' in self.table_df.columns and end_col + 'Т2' in self.table_df.columns) or \
                        (end_col + 'T1' in self.table_df.columns and end_col + 'T2' in self.table_df.columns):
                    filter_cols.append(end_col + 'T1')
                    filter_cols.append(end_col + 'T2')

            filter_cols = list(filter_cols)
            self.table_df = self.table_df[filter_cols]

        self.tables[param] = self.table_df
        self._try_to_create_new_fields_for_table(param, inputs)

    def _f_ra_concatenation_left(self, param, inputs):
        try:
            if list(inputs['parsed_params']['Таблица_1'].values())[0]['type'] == 'Функция':
                tbl_name_1 = list(inputs['parsed_params']['Таблица_1'].values())[0]['linked_by_table']
            else:
                tbl_name_1 = list(inputs['parsed_params']['Таблица_1'].keys())[0]
            if list(inputs['parsed_params']['Таблица_2'].values())[0]['type'] == 'Функция':
                tbl_name_2 = list(inputs['parsed_params']['Таблица_2'].values())[0]['linked_by_table']
            else:
                tbl_name_2 = list(inputs['parsed_params']['Таблица_2'].keys())[0]
            merge_on_left = list(inputs['parsed_params']['Объединить_по_столбцу_слева'].keys())
            merge_on_right = list(inputs['parsed_params']['Объединить_по_столбцу_справа'].keys())
            end_cols = list(inputs['parsed_params'].get('Результирующие_поля', {}).keys())
        except KeyError:
            raise KeyError('Указаны не все параметры')
        df1 = self.tables.get(tbl_name_1)
        df2 = self.tables.get(tbl_name_2)
        if df1 is not None and df2 is not None:
            if not merge_on_left or not merge_on_right:
                self.table_df = df1.merge(df2, how='cross', suffixes=['T1', 'T2'])
            else:
                self.table_df = df1.merge(df2, left_on=merge_on_left, right_on=merge_on_right,
                                          how='left', suffixes=['T1', 'T2'])
        else:
            raise ValueError('undefined')

        if end_cols:
            filter_cols = []
            for end_col in end_cols:
                if end_col in self.table_df.columns:
                    filter_cols.append(end_col)
                elif (end_col + 'Т1' in self.table_df.columns and end_col + 'Т2' in self.table_df.columns) or \
                        (end_col + 'T1' in self.table_df.columns and end_col + 'T2' in self.table_df.columns):
                    filter_cols.append(end_col + 'T1')
                    filter_cols.append(end_col + 'T2')

            filter_cols = list(filter_cols)
            self.table_df = self.table_df[filter_cols]

        self.tables[param] = self.table_df
        self._try_to_create_new_fields_for_table(param, inputs)

    def _f_ra_concatenation(self, param, inputs):
        try:
            if list(inputs['parsed_params']['Таблица_1'].values())[0]['type'] == 'Функция':
                tbl_name_1 = list(inputs['parsed_params']['Таблица_1'].values())[0]['linked_by_table']
            else:
                tbl_name_1 = list(inputs['parsed_params']['Таблица_1'].keys())[0]
            if list(inputs['parsed_params']['Таблица_2'].values())[0]['type'] == 'Функция':
                tbl_name_2 = list(inputs['parsed_params']['Таблица_2'].values())[0]['linked_by_table']
            else:
                tbl_name_2 = list(inputs['parsed_params']['Таблица_2'].keys())[0]
            merge_on_left = list(inputs['parsed_params']['Объединить_по_столбцу_слева'].keys())
            merge_on_right = list(inputs['parsed_params']['Объединить_по_столбцу_справа'].keys())
            end_cols = list(inputs['parsed_params'].get('Результирующие_поля', {}).keys())
        except KeyError:
            raise KeyError('Указаны не все параметры')
        df1 = self.tables.get(tbl_name_1)
        df2 = self.tables.get(tbl_name_2)
        if df1 is not None and df2 is not None:
            if not merge_on_left or not merge_on_right:
                self.table_df = df1.merge(df2, how='cross', suffixes=['T1', 'T2'])
            else:
                self.table_df = df1.merge(df2, left_on=merge_on_left, right_on=merge_on_right, suffixes=['T1', 'T2'])
        else:
            raise ValueError('undefined')

        if end_cols:
            filter_cols = []
            for end_col in end_cols:
                if end_col in self.table_df.columns:
                    filter_cols.append(end_col)
                elif (end_col + 'Т1' in self.table_df.columns and end_col + 'Т2' in self.table_df.columns) or \
                        (end_col + 'T1' in self.table_df.columns and end_col + 'T2' in self.table_df.columns):
                    filter_cols.append(end_col + 'T1')
                    filter_cols.append(end_col + 'T2')

            filter_cols = list(filter_cols)
            self.table_df = self.table_df[filter_cols]

        self.tables[param] = self.table_df
        self._try_to_create_new_fields_for_table(param, inputs)

    def _f_ra_copy(self, param, inputs):
        ret_type = inputs['ret_type']
        if ret_type == 'Поле':
            self._f_ra_copy_as_field(param, inputs)
        else:
            self._f_ra_copy_as_table(param, inputs)

    def _f_ra_copy_as_field(self, param, inputs):
        old_col = inputs['parsed_params']['Поле']
        old_col = list(old_col.keys())[0]
        self.table_df[param] = self.table_df[old_col]
        self._filter_runtime_fields({old_col: list(inputs['parsed_params']['Поле'].values())[0]})

    def _f_ra_copy_as_table(self, param, inputs):
        if list(inputs['parsed_params']['Таблица'].values())[0]['type'] == 'Функция':
            old_tbl = list(inputs['parsed_params']['Таблица'].values())[0]['linked_by_table']
        else:
            old_tbl = list(inputs['parsed_params']['Таблица'].keys())[0]
        end_cols = list(inputs['parsed_params'].get('Результирующие_поля', {}).keys())
        self.tables[param] = self.table_df = self.tables[old_tbl]

        if end_cols:
            filter_cols = []
            for end_col in end_cols:
                if end_col in self.table_df.columns:
                    filter_cols.append(end_col)

            filter_cols = list(filter_cols)
            self.table_df = self.table_df[filter_cols]

        self._try_to_create_new_fields_for_table(param, inputs)

    def _f_agr_cumsum(self, param, inputs):
        if inputs['ret_type'] == 'Таблица':
            self._f_agr_cumsum_as_table(param, inputs)
        else:
            self._f_agr_cumsum_as_field(param, inputs)

    def _f_agr_cumsum_as_table(self, param, inputs):
        cols = inputs['parsed_params']['Агрегируемый_показатель']
        cols = list(cols.keys())
        cols_for_group_by = inputs['parsed_params']['Измерения']
        cols_for_group_by = list(cols_for_group_by.keys())

        if not cols_for_group_by:
            for col in cols:
                self.table_df[col] = self.table_df[col].cumsum()
        else:
            for col in cols:
                _cols = [col]
                _cols.extend(cols_for_group_by)
                self.table_df[col] = self.table_df[_cols].groupby(cols_for_group_by, as_index=False).cumsum()

        self._try_to_create_new_fields_for_table(param, inputs)

    def _f_agr_cumsum_as_field(self, param, inputs):
        cols_for_group_by = inputs['parsed_params']['Измерения']
        cols_for_group_by = list(cols_for_group_by.keys())
        cols = inputs['parsed_params']['Агрегируемый_показатель']
        col = list(cols.keys())[0]

        if not cols_for_group_by:
            self.table_df[col] = self.table_df[col].cumsum()
        else:
            _cols = [col]
            _cols.extend(cols_for_group_by)
            self.table_df[col] = self.table_df[_cols].groupby(cols_for_group_by, as_index=False).cumsum()

        self._filter_runtime_fields(inputs['parsed_params']['Измерения'])

    def _f_agr_avg(self, param, inputs):
        ret_type = inputs['ret_type']
        if ret_type == 'Поле':
            self._f_agr_avg_as_field(param, inputs)
        else:
            self._f_agr_avg_as_table(param, inputs)

    def _f_agr_avg_as_field(self, param, inputs):
        cols = inputs['parsed_params']['Измерения']
        self.table_df[param] = self.table_df[list(cols.keys())].apply(lambda x: x.mean(), axis=1)
        self._filter_runtime_fields(inputs['parsed_params']['Измерения'])

    def _f_agr_avg_as_table(self, param, inputs):
        cols = inputs['parsed_params']['Агрегируемый_показатель']
        cols = list(cols.keys())
        cols_for_group_by = inputs['parsed_params']['Измерения']
        cols_for_group_by = list(cols_for_group_by.keys())

        if cols_for_group_by == []:
            self.table_df = self.table_df[cols].mean().to_dict()
            self.table_df = pd.DataFrame([list(self.table_df.values())], columns=list(self.table_df.keys()))
        else:
            cols.extend(cols_for_group_by)
            self.table_df = self.table_df[cols].groupby(cols_for_group_by, as_index=False).mean()

        self._try_to_create_new_fields_for_table(param, inputs)

    def _f_agr_sum(self, param, inputs):
        ret_type = inputs['ret_type']
        if ret_type == 'Поле':
            self._f_agr_sum_as_field(param, inputs)
        else:
            self._f_agr_sum_as_table(param, inputs)

    def _f_agr_sum_as_field(self, param, inputs):
        cols = inputs['parsed_params']['Измерения']
        self.table_df[param] = self.table_df[list(cols.keys())].apply(lambda x: x.sum(), axis=1)
        self._filter_runtime_fields(inputs['parsed_params']['Измерения'])

    def _f_agr_sum_as_table(self, param, inputs):
        cols = inputs['parsed_params']['Агрегируемый_показатель']
        cols = list(cols.keys())
        cols_for_group_by = inputs['parsed_params']['Измерения']
        cols_for_group_by = list(cols_for_group_by.keys())

        if cols_for_group_by == []:
            self.table_df = self.table_df[cols].sum().to_dict()
            self.table_df = pd.DataFrame([list(self.table_df.values())], columns=list(self.table_df.keys()))
        else:
            cols.extend(cols_for_group_by)
            self.table_df = self.table_df[cols].groupby(cols_for_group_by, as_index=False).sum()

        self._try_to_create_new_fields_for_table(param, inputs)

    def _f_agr_count(self, param, inputs):
        ret_type = inputs['ret_type']
        if ret_type == 'Поле':
            self._f_agr_count_as_field(param, inputs)
        else:
            self._f_agr_count_as_table(param, inputs)

    def _f_agr_count_as_field(self, param, inputs):
        cols = inputs['parsed_params']['Измерения']
        self.table_df[param] = self.table_df[list(cols.keys())].apply(lambda x: x.count(), axis=1)
        self._filter_runtime_fields(inputs['parsed_params']['Измерения'])

    def _f_agr_count_as_table(self, param, inputs):
        cols = inputs['parsed_params']['Агрегируемый_показатель']
        cols = list(cols.keys())
        cols_for_group_by = inputs['parsed_params']['Измерения']
        cols_for_group_by = list(cols_for_group_by.keys())

        if cols_for_group_by == []:
            self.table_df = self.table_df[cols].count().to_dict()
            self.table_df = pd.DataFrame([list(self.table_df.values())], columns=list(self.table_df.keys()))
        else:
            cols.extend(cols_for_group_by)
            self.table_df = self.table_df[cols].groupby(cols_for_group_by, as_index=False).count()

        self._try_to_create_new_fields_for_table(param, inputs)

    def _f_agr_nunique(self, param, inputs):
        ret_type = inputs['ret_type']
        if ret_type == 'Поле':
            self._f_agr_nunique_as_field(param, inputs)
        else:
            self._f_agr_nunique_as_table(param, inputs)

    def _f_agr_nunique_as_field(self, param, inputs):
        cols = inputs['parsed_params']['Измерения']
        self.table_df[param] = self.table_df[list(cols.keys())].apply(lambda x: x.nunique(), axis=1)
        self._filter_runtime_fields(inputs['parsed_params']['Измерения'])

    def _f_agr_nunique_as_table(self, param, inputs):
        cols = inputs['parsed_params']['Агрегируемый_показатель']
        cols = list(cols.keys())
        cols_for_group_by = inputs['parsed_params']['Измерения']
        cols_for_group_by = list(cols_for_group_by.keys())

        if cols_for_group_by == []:
            self.table_df = self.table_df[cols].nunique().to_dict()
            self.table_df = pd.DataFrame([list(self.table_df.values())], columns=list(self.table_df.keys()))
        else:
            cols.extend(cols_for_group_by)
            self.table_df = self.table_df[cols].groupby(cols_for_group_by, as_index=False).nunique()

        self._try_to_create_new_fields_for_table(param, inputs)

    def _f_agr_min(self, param, inputs):
        ret_type = inputs['ret_type']
        if ret_type == 'Поле':
            self._f_agr_min_as_field(param, inputs)
        else:
            self._f_agr_min_as_table(param, inputs)

    def _f_agr_min_as_field(self, param, inputs):
        cols = inputs['parsed_params']['Измерения']
        self.table_df[param] = self.table_df[list(cols.keys())].apply(lambda x: x.min(), axis=1)
        self._filter_runtime_fields(inputs['parsed_params']['Измерения'])

    def _f_agr_min_as_table(self, param, inputs):
        cols = inputs['parsed_params']['Агрегируемый_показатель']
        cols = list(cols.keys())
        cols_for_group_by = inputs['parsed_params']['Измерения']
        cols_for_group_by = list(cols_for_group_by.keys())

        if cols_for_group_by == []:
            self.table_df = self.table_df[cols].min().to_dict()
            self.table_df = pd.DataFrame([list(self.table_df.values())], columns=list(self.table_df.keys()))
        else:
            cols.extend(cols_for_group_by)
            self.table_df = self.table_df[cols].groupby(cols_for_group_by, as_index=False).min()

        self._try_to_create_new_fields_for_table(param, inputs)

    def _f_agr_max(self, param, inputs):
        ret_type = inputs['ret_type']
        if ret_type == 'Поле':
            self._f_agr_max_as_field(param, inputs)
        else:
            self._f_agr_max_as_table(param, inputs)

    def _f_agr_max_as_field(self, param, inputs):
        cols = inputs['parsed_params']['Измерения']
        self.table_df[param] = self.table_df[list(cols.keys())].apply(lambda x: x.max(), axis=1)
        self._filter_runtime_fields(inputs['parsed_params']['Измерения'])

    def _f_agr_max_as_table(self, param, inputs):
        cols = inputs['parsed_params']['Агрегируемый_показатель']
        cols = list(cols.keys())
        cols_for_group_by = inputs['parsed_params']['Измерения']
        cols_for_group_by = list(cols_for_group_by.keys())

        if cols_for_group_by == []:
            self.table_df = self.table_df[cols].max().to_dict()
            self.table_df = pd.DataFrame([list(self.table_df.values())], columns=list(self.table_df.keys()))
        else:
            cols.extend(cols_for_group_by)
            self.table_df = self.table_df[cols].groupby(cols_for_group_by, as_index=False).max()

        self._try_to_create_new_fields_for_table(param, inputs)

    def _f_agr_median(self, param, inputs):
        ret_type = inputs['ret_type']
        if ret_type == 'Поле':
            self._f_agr_median_as_field(param, inputs)
        else:
            self._f_agr_median_as_table(param, inputs)

    def _f_agr_median_as_field(self, param, inputs):
        cols = inputs['parsed_params']['Измерения']
        self.table_df[param] = self.table_df[list(cols.keys())].apply(lambda x: x.median(), axis=1)
        self._filter_runtime_fields(inputs['parsed_params']['Измерения'])

    def _f_agr_median_as_table(self, param, inputs):
        cols = inputs['parsed_params']['Агрегируемый_показатель']
        cols = list(cols.keys())
        cols_for_group_by = inputs['parsed_params']['Измерения']
        cols_for_group_by = list(cols_for_group_by.keys())

        if cols_for_group_by == []:
            self.table_df = self.table_df[cols].median().to_dict()
            self.table_df = pd.DataFrame([list(self.table_df.values())], columns=list(self.table_df.keys()))
        else:
            cols.extend(cols_for_group_by)
            self.table_df = self.table_df[cols].groupby(cols_for_group_by, as_index=False).median()

        self._try_to_create_new_fields_for_table(param, inputs)

    def _f_ad_corr(self, param, inputs):
        ret_type = inputs['ret_type']
        if ret_type == 'Поле':
            self._f_ad_corr_as_field(param, inputs)
        else:
            self._f_ad_corr_as_table(param, inputs)

    def _f_ad_corr_as_field(self, param, inputs):
        cols = inputs['parsed_params']['Измерения']
        cols = list(cols.keys())
        if len(cols) == 2:
            # corr = self.table_df[cols[0]].corr(self.table_df[cols[1]])
            self.table_df[param] = self.table_df[cols[0]].corr(self.table_df[cols[1]])
        else:
            raise ValueError('Для корелляции необходимо указать два измерения')

        self._filter_runtime_fields(inputs['parsed_params']['Измерения'])

    def _f_ad_corr_as_table(self, param, inputs):
        cols = inputs['parsed_params']['Измерения']
        cols = list(cols.keys())

        if len(cols) == 2:
            new_col = 'corr_' + '__'.join(cols)
            self.table_df = pd.DataFrame([self.table_df[cols[0]].corr(self.table_df[cols[1]])], columns=[new_col])
        else:
            raise ValueError('Для корелляции необходимо указать два измерения')

        self._try_to_create_new_fields_for_table(param, inputs)

    def _f_ad_rang_corr(self, param, inputs):
        cols = inputs['parsed_params']['Измерения']
        cols = list(cols.keys())

        try:
            import scipy
            if len(cols) == 2:
                rho, p = scipy.stats.spearmanr(self.table_df[cols[0]], self.table_df[cols[1]])
                # rho = scipy.stats.spearmanr(self.table_df[cols[0]], self.table_df[cols[1]])[0]
                self.table_df = pd.DataFrame([[rho, p]], columns=['_spearmanr', 'p-value'])
            else:
                raise ValueError('Для корелляции необходимо указать два измерения')
        except Exception:
            if len(cols) == 2:
                rho = self.table_df[cols[0]].corr(self.table_df[cols[1]], method='spearman')
                self.table_df = pd.DataFrame([[rho]], columns=['_spearmanr'])
            else:
                raise ValueError('Для корелляции необходимо указать два измерения')

        self._try_to_create_new_fields_for_table(param, inputs)

    def _f_ad_partial_corr(self, param, inputs):
        try:
            import pingouin
        except Exception:
            pass

        cols = inputs['parsed_params']['Измерения']
        cols = list(cols.keys())[:2]
        covar = inputs['parsed_params']['Контролируемая_переменная']
        covar = list(covar.keys())[0]
        self.table_df = pingouin.partial_corr(data=self.table_df, x=cols[0], y=cols[1], covar=covar)
        self.table_df['CI95%_min'] = self.table_df['CI95%'][0][0]
        self.table_df['CI95%_max'] = self.table_df['CI95%'][0][1]
        self.table_df.drop('CI95%', axis=1, inplace=True)

        self._try_to_create_new_fields_for_table(param, inputs)

    def _f_pr_value(self, param, inputs):
        val_name = list(inputs['parsed_params']['Значение'].keys())[0]
        val = {
            'type': inputs['parsed_params']['Значение'][val_name]['type'],
            'self_name': val_name,
            'value': inputs['parsed_params']['Значение'][val_name].get('value', None)
        }

        self.table_df[param] = fast_real(val['value'])

    def _f_pr_nan(self, param, inputs, is_ds=False):
        if is_ds:
            return 'np.nan'
        else:
            return np.nan

    def _f_rsd_set_date_from_parts(self, param, inputs):
        try:
            year_name = list(inputs['parsed_params']['Год'].keys())[0]
            year = {
                'type': inputs['parsed_params']['Год'][year_name]['type'],
                'self_name': year_name,
                'value': inputs['parsed_params']['Год'][year_name].get('value', None)
            }
            month_name = list(inputs['parsed_params']['Месяц'].keys())[0]
            month = {
                'type': inputs['parsed_params']['Месяц'][month_name]['type'],
                'self_name': month_name,
                'value': inputs['parsed_params']['Месяц'][month_name].get('value', None)
            }
            day_name = list(inputs['parsed_params']['День'].keys())[0]
            day = {
                'type': inputs['parsed_params']['День'][day_name]['type'],
                'self_name': day_name,
                'value': inputs['parsed_params']['День'][day_name].get('value', None)
            }
        except KeyError:
            raise Exception('[ADF] В функции Сбор_даты указаны не все параметры')

        row_count = self.table_df.shape[0]
        year_param = self.table_df[year_name] if year['type'] != 'Значение' else [year['value']] * row_count
        month_param = self.table_df[month_name] if month['type'] != 'Значение' else [month['value']] * row_count
        day_param = self.table_df[day_name] if day['type'] != 'Значение' else [day['value']] * row_count
        self.table_df[param] = pd.to_datetime(pd.DataFrame({
            'year': year_param,
            'month': month_param,
            'day': day_param
        }))
        runtime_fields = {
            year_name: year,
            month_name: month,
            day_name: day
        }
        self._filter_runtime_fields(runtime_fields)

    def _f_rsd_set_datetime_from_parts(self, param, inputs):
        runtime_fields = {}
        row_count = self.table_df.shape[0]
        try:
            year_name = list(inputs['parsed_params']['Год'].keys())[0]
            year = {
                'type': inputs['parsed_params']['Год'][year_name]['type'],
                'self_name': year_name,
                'value': inputs['parsed_params']['Год'][year_name].get('value', None)
            }
            if year['type'] != 'Значение':
                runtime_fields[year_name] = year
            year_param = self.table_df[year_name] if year['type'] != 'Значение' else [year['value']] * row_count

            month_name = list(inputs['parsed_params']['Месяц'].keys())[0]
            month = {
                'type': inputs['parsed_params']['Месяц'][month_name]['type'],
                'self_name': month_name,
                'value': inputs['parsed_params']['Месяц'][month_name].get('value', None)
            }
            if month['type'] != 'Значение':
                runtime_fields[month_name] = month
            month_param = self.table_df[month_name] if month['type'] != 'Значение' else [month['value']] * row_count

            day_name = list(inputs['parsed_params']['День'].keys())[0]
            day = {
                'type': inputs['parsed_params']['День'][day_name]['type'],
                'self_name': day_name,
                'value': inputs['parsed_params']['День'][day_name].get('value', None)
            }
            if day['type'] != 'Значение':
                runtime_fields[day_name] = day
            day_param = self.table_df[day_name] if day['type'] != 'Значение' else [day['value']] * row_count
        except KeyError:
            raise Exception('[ADF] В функции Сбор_даты указаны не все параметры')
        if inputs['parsed_params']['Час'].keys():
            hour_name = list(inputs['parsed_params']['Час'].keys())[0]
            hour = {
                'type': inputs['parsed_params']['Час'][hour_name]['type'],
                'self_name': hour_name,
                'value': inputs['parsed_params']['Час'][hour_name].get('value', None)
            }
            if hour['type'] != 'Значение':
                runtime_fields[hour_name] = hour
            hour_param = self.table_df[day_name] if hour['type'] != 'Значение' else [hour['value']] * row_count
        else:
            hour_param = 0
        if inputs['parsed_params']['Минута'].keys():
            minute_name = list(inputs['parsed_params']['Минута'].keys())[0]
            minute = {
                'type': inputs['parsed_params']['Минута'][minute_name]['type'],
                'self_name': minute_name,
                'value': inputs['parsed_params']['Минута'][minute_name].get('value', None)
            }
            if minute['type'] != 'Значение':
                runtime_fields[minute_name] = minute
            minute_param = self.table_df[minute_name] if minute['type'] != 'Значение' else [minute['value']] * row_count
        else:
            minute_param = 0
        if inputs['parsed_params']['Секунда'].keys():
            second_name = list(inputs['parsed_params']['Секунда'].keys())[0]
            second = {
                'type': inputs['parsed_params']['Секунда'][second_name]['type'],
                'self_name': second_name,
                'value': inputs['parsed_params']['Секунда'][second_name].get('value', None)
            }
            if second['type'] != 'Значение':
                runtime_fields[second_name] = second
            second_param = self.table_df[second_name] if second['type'] != 'Значение' else [second['value']] * row_count
        else:
            second_param = 0

        self.table_df[param] = pd.to_datetime(pd.DataFrame({
            'year': year_param,
            'month': month_param,
            'day': day_param,
            'hour': hour_param,
            'minute': minute_param,
            'second': second_param
        }))
        self._filter_runtime_fields(runtime_fields)

    def _f_rsd_get_year_from_date(self, param, inputs):
        col_name = list(inputs['parsed_params']['Измерение'].keys())[0]
        col = list(inputs['parsed_params']['Измерение'].values())[0]
        self.table_df[param] = self.table_df[col_name].dt.year
        self._filter_runtime_fields({col_name: col})

    def _f_rsd_get_month_from_date(self, param, inputs):
        col_name = list(inputs['parsed_params']['Измерение'].keys())[0]
        col = list(inputs['parsed_params']['Измерение'].values())[0]
        self.table_df[param] = self.table_df[col_name].dt.month
        self._filter_runtime_fields({col_name: col})

    def _f_rsd_get_day_from_date(self, param, inputs):
        col_name = list(inputs['parsed_params']['Измерение'].keys())[0]
        col = list(inputs['parsed_params']['Измерение'].values())[0]
        self.table_df[param] = self.table_df[col_name].dt.day
        self._filter_runtime_fields({col_name: col})

    def _f_rsd_get_hour_from_date(self, param, inputs):
        col_name = list(inputs['parsed_params']['Измерение'].keys())[0]
        col = list(inputs['parsed_params']['Измерение'].values())[0]
        self.table_df[param] = self.table_df[col_name].dt.hour
        self._filter_runtime_fields({col_name: col})

    def _f_rsd_get_minute_from_date(self, param, inputs):
        col_name = list(inputs['parsed_params']['Измерение'].keys())[0]
        col = list(inputs['parsed_params']['Измерение'].values())[0]
        self.table_df[param] = self.table_df[col_name].dt.minute
        self._filter_runtime_fields({col_name: col})

    def _f_rsd_get_second_from_date(self, param, inputs):
        col_name = list(inputs['parsed_params']['Измерение'].keys())[0]
        col = list(inputs['parsed_params']['Измерение'].values())[0]
        self.table_df[param] = self.table_df[col_name].dt.second
        self._filter_runtime_fields({col_name: col})

    def _f_rsd_start_day(self, param, inputs):
        col_name = list(inputs['parsed_params']['Измерение'].keys())[0]
        col = list(inputs['parsed_params']['Измерение'].values())[0]
        self.table_df[param] = self.table_df[col_name].dt.to_period('D').apply(lambda r: r.start_time)
        self._filter_runtime_fields({col_name: col})

    def _f_rsd_start_week(self, param, inputs):
        col_name = list(inputs['parsed_params']['Измерение'].keys())[0]
        col = list(inputs['parsed_params']['Измерение'].values())[0]
        self.table_df[param] = self.table_df[col_name].dt.to_period('W').apply(lambda r: r.start_time)
        self._filter_runtime_fields({col_name: col})

    def _f_rsd_start_month(self, param, inputs):
        col_name = list(inputs['parsed_params']['Измерение'].keys())[0]
        col = list(inputs['parsed_params']['Измерение'].values())[0]
        self.table_df[param] = self.table_df[col_name].dt.to_period('M').apply(lambda r: r.start_time)
        self._filter_runtime_fields({col_name: col})

    def _f_rsd_start_year(self, param, inputs):
        col_name = list(inputs['parsed_params']['Измерение'].keys())[0]
        col = list(inputs['parsed_params']['Измерение'].values())[0]
        self.table_df[param] = self.table_df[col_name].dt.to_period('Y').apply(lambda r: r.start_time)
        self._filter_runtime_fields({col_name: col})

    def _try_to_create_new_fields_for_table(self, param, inputs):
        if inputs['parsed_params'].get('Таблица') is not None:
            if list(inputs['parsed_params']['Таблица'].values())[0]['type'] == 'Функция':
                named_tbl = list(inputs['parsed_params']['Таблица'].values())[0]['linked_by_table']
            else:
                named_tbl = list(inputs['parsed_params']['Таблица'].keys())[0]

            self.operands['tables'][param]['fields'] = {
                k: v for k, v in self.operands['tables'][param]['fields'].items()
                if v['is_in'] is False or self._get_prev_name_for_column(v) in self.table_df.columns
            }
            parent_child = {
                self._get_prev_name_for_column(v): k for k, v in self.operands['tables'][param]['fields'].items()
            }
            self.table_df.rename(columns=parent_child, inplace=True)
            for col in self.table_df.columns:
                if self.operands['tables'][param]['fields'].get(col) is None:
                    new_fld_name = self._get_unique_column(col)
                    if self.operands['tables'][named_tbl]['fields'].get(col) is not None:
                        self.operands['tables'][param]['fields'][new_fld_name] = {
                            'self_name': new_fld_name,
                            'display_name': f"{self.operands['tables'][param]['display_name']}."
                                            f"{self.operands['tables'][named_tbl]['fields'][col]['display_name']}",
                            'parent': col,
                            'type': 'Поле',
                            'is_in': True,
                            'expression': {}
                        }
                    else:
                        self.operands['tables'][param]['fields'][new_fld_name] = {
                            'self_name': new_fld_name,
                            'display_name': f"{self.operands['tables'][param]['display_name']}.{new_fld_name}",
                            'parent': col,
                            'type': 'Поле',
                            'is_in': True,
                            'expression': {}
                        }
        elif inputs['parsed_params'].get('Таблица_1') is not None and \
                inputs['parsed_params'].get('Таблица_2') is not None:

            if list(inputs['parsed_params']['Таблица_1'].values())[0]['type'] == 'Функция':
                named_tbl_1 = list(inputs['parsed_params']['Таблица_1'].values())[0]['linked_by_table']
            else:
                named_tbl_1 = list(inputs['parsed_params']['Таблица_1'].keys())[0]

            if list(inputs['parsed_params']['Таблица_2'].values())[0]['type'] == 'Функция':
                named_tbl_2 = list(inputs['parsed_params']['Таблица_2'].values())[0]['linked_by_table']
            else:
                named_tbl_2 = list(inputs['parsed_params']['Таблица_2'].keys())[0]

            named_fields = dict()
            named_fields.update(self.operands['tables'][named_tbl_1]['fields'])
            named_fields.update(self.operands['tables'][named_tbl_2]['fields'])
            self.operands['tables'][param]['fields'] = {
                k: v for k, v in self.operands['tables'][param]['fields'].items()
                if v['is_in'] is False or self._get_prev_name_for_column(v) in self.table_df.columns
            }
            parent_child = {
                self._get_prev_name_for_column(v): k for k, v in self.operands['tables'][param]['fields'].items()
            }
            self.table_df.rename(columns=parent_child, inplace=True)
            for col in self.table_df.columns:
                if self.operands['tables'][param]['fields'].get(col) is None:
                    new_fld_name = self._get_unique_column(col)
                    if named_fields.get(col) is not None:
                        self.operands['tables'][param]['fields'][new_fld_name] = {
                            'self_name': new_fld_name,
                            'display_name': f"{self.operands['tables'][param]['display_name']}."
                                            f"{named_fields[col]['display_name']}",
                            'parent': col,
                            'type': 'Поле',
                            'is_in': True,
                            'expression': {}
                        }
                    elif named_fields.get(col[:-2]) is not None:
                        suffix = col[-2:]
                        d_n = named_fields.get(col[:-2])['display_name'] + suffix
                        s_n = named_fields.get(col[:-2])['self_name'] + suffix
                        s_n = self._get_unique_column(s_n)
                        self.operands['tables'][param]['fields'][s_n] = {
                            'self_name': s_n,
                            'display_name': f"{self.operands['tables'][param]['display_name']}.{d_n}",
                            'parent': col,
                            'type': 'Поле',
                            'is_in': True,
                            'expression': {}
                        }
                    else:
                        self.operands['tables'][param]['fields'][new_fld_name] = {
                            'self_name': new_fld_name,
                            'display_name': f"{self.operands['tables'][param]['display_name']}.{new_fld_name}",
                            'parent': col,
                            'type': 'Поле',
                            'is_in': True,
                            'expression': {}
                        }

        parent_child = {
            self._get_prev_name_for_column(v): k for k, v in self.operands['tables'][param]['fields'].items()
        }
        self.table_df.rename(columns=parent_child, inplace=True)
        self._transform_to_datetime()
        self._save_operands(self.operands)

    def _get_unique_column(self, _fld):
        used_fields = dict()
        for tbl, tbl_opt in self.operands['tables'].items():
            for fld in tbl_opt['fields'].keys():
                used_fields[fld] = fld
            used_fields[tbl] = tbl

        if used_fields.get(_fld):
            _field_name = self.new_name(_fld, used_fields)
        else:
            _field_name = _fld

        return _field_name

    def _get_prev_name_for_column(self, fld):
        return fld.get('parent', fld['self_name'])

    def _get_func_opt(self, _func):
        for wrap, func_dict in self.options['functions'].items():
            for func_name, opts in func_dict.items():
                if func_name == _func:
                    return opts
        return None

    def _get_tbl_opt(self):
        tbl_opt = {k: {
            'self_name': v['self_name'],
            'display_name': v['display_name'],
            'type': v['type'],
            'is_in': v['is_in']
        } for k, v in self.operands['tables'].items() if v.get('hidden') is None or v.get('hidden') is False}
        return tbl_opt

    def _get_fld_opt(self):
        tables = self.operands['tables'].copy()
        tables.update(self.tried_to_calculate)
        fld_opt = {k: {
            'self_name': v['self_name'],
            'display_name': v['display_name'],
            'type': v['type'],
            'is_in': v['is_in'],
            'fields': {k1: {
                'self_name': v1['self_name'],
                'display_name': v1['display_name'],
                'type': v1['type']
            } for k1, v1 in v['fields'].items()}
        } for k, v in tables.items()}
        return fld_opt

    def _init_options(self):
        self.options = {
            'operands': self.operands,
            'functions': {
                'Функции_агрегирования': {
                    'Медиана': {
                        'type': 'Функция',
                        'backend_method': '_f_agr_median',
                        'return_type': ['Таблица', 'Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Таблица': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Таблица': {},
                                        'Функция': {}
                                    }
                                },
                                'Измерения': {
                                    'values': {},
                                    'if_return_type': ['Таблица', 'Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {}
                                    }
                                },
                                'Агрегируемый_показатель': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Поле': {}
                                    }
                                }
                            }
                        }
                    },
                    'Среднее': {
                        'type': 'Функция',
                        'backend_method': '_f_agr_avg',
                        'return_type': ['Таблица', 'Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Таблица': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Таблица': {},
                                        'Функция': {}
                                    }
                                },
                                'Измерения': {
                                    'values': {},
                                    'if_return_type': ['Таблица', 'Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {}
                                    }
                                },
                                'Агрегируемый_показатель': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Поле': {}
                                    }
                                }
                            }
                        }
                    },
                    'АГР_Сумма': {
                        'type': 'Функция',
                        'backend_method': '_f_agr_sum',
                        'return_type': ['Таблица', 'Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Таблица': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Таблица': {},
                                        'Функция': {}
                                    }
                                },
                                'Измерения': {
                                    'values': {},
                                    'if_return_type': ['Таблица', 'Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {}
                                    }
                                },
                                'Агрегируемый_показатель': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Поле': {}
                                    }
                                }
                            }
                        }
                    },
                    'Количество': {
                        'type': 'Функция',
                        'backend_method': '_f_agr_count',
                        'return_type': ['Таблица', 'Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Таблица': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Таблица': {},
                                        'Функция': {}
                                    }
                                },
                                'Измерения': {
                                    'values': {},
                                    'if_return_type': ['Таблица', 'Поле'],
                                    '__possible_values__': {
                                        'Поле': {}
                                    }
                                },
                                'Агрегируемый_показатель': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Поле': {}
                                    }
                                }
                            }
                        }
                    },
                    'Количество_уникальных': {
                        'type': 'Функция',
                        'backend_method': '_f_agr_nunique',
                        'return_type': ['Таблица', 'Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Таблица': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Таблица': {},
                                        'Функция': {}
                                    }
                                },
                                'Измерения': {
                                    'values': {},
                                    'if_return_type': ['Таблица', 'Поле'],
                                    '__possible_values__': {
                                        'Поле': {}
                                    }
                                },
                                'Агрегируемый_показатель': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Поле': {}
                                    }
                                }
                            }
                        }
                    },
                    'Минимум': {
                        'type': 'Функция',
                        'backend_method': '_f_agr_min',
                        'return_type': ['Таблица', 'Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Таблица': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Таблица': {},
                                        'Функция': {}
                                    }
                                },
                                'Измерения': {
                                    'values': {},
                                    'if_return_type': ['Таблица', 'Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {}
                                    }
                                },
                                'Агрегируемый_показатель': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Поле': {}
                                    }
                                }
                            }
                        }
                    },
                    'Максимум': {
                        'type': 'Функция',
                        'backend_method': '_f_agr_max',
                        'return_type': ['Таблица', 'Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Таблица': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Таблица': {},
                                        'Функция': {}
                                    }
                                },
                                'Измерения': {
                                    'values': {},
                                    'if_return_type': ['Таблица', 'Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {}
                                    }
                                },
                                'Агрегируемый_показатель': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Поле': {}
                                    }
                                }
                            }
                        }
                    },
                    'Кумулятивная_сумма': {
                        'type': 'Функция',
                        'backend_method': '_f_agr_cumsum',
                        'return_type': ['Поле', 'Таблица'],
                        'tree_struct': {
                            'Параметры': {
                                'Таблица': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Таблица': {},
                                        'Функция': {}
                                    }
                                },
                                'Измерения': {
                                    'values': {},
                                    'if_return_type': ['Поле', 'Таблица'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {}
                                    }
                                },
                                'Агрегируемый_показатель': {
                                    'values': {},
                                    'if_return_type': ['Таблица', 'Поле'],
                                    '__possible_values__': {
                                        'Поле': {}
                                    }
                                }
                            }
                        }
                    }
                },
                'Анализ_данных': {
                    'Корреляция': {
                        'type': 'Функция',
                        'backend_method': '_f_ad_corr',
                        'return_type': ['Таблица', 'Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Таблица': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Таблица': {},
                                        'Функция': {}
                                    }
                                },
                                'Измерения': {
                                    'values': {},
                                    'if_return_type': ['Таблица', 'Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {}
                                    }
                                }
                            }
                        }
                    },
                    'Ранговая_корреляция': {
                        'type': 'Функция',
                        'backend_method': '_f_ad_rang_corr',
                        'return_type': ['Таблица'],
                        'tree_struct': {
                            'Параметры': {
                                'Таблица': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Таблица': {},
                                        'Функция': {}
                                    }
                                },
                                'Измерения': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {}
                                    }
                                }
                            }
                        }
                    },
                    'Частичная_корреляция': {
                        'type': 'Функция',
                        'backend_method': '_f_ad_partial_corr',
                        'return_type': ['Таблица'],
                        'tree_struct': {
                            'Параметры': {
                                'Таблица': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Таблица': {},
                                        'Функция': {}
                                    }
                                },
                                'Измерения': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {}
                                    }
                                },
                                'Контролируемая_переменная': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {}
                                    }
                                }
                            }
                        }
                    }
                },
                'Арифметические_операции': {
                    'Сумма': {
                        'type': 'Функция',
                        'backend_method': '_f_ao_sum',
                        'return_type': ['Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Левый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Значение': {},
                                        'Функция': {}
                                    }
                                },
                                'Правый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Значение': {},
                                        'Функция': {}
                                    }
                                }
                            }
                        }
                    },
                    'Разность': {
                        'type': 'Функция',
                        'backend_method': '_f_ao_difference',
                        'return_type': ['Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Левый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Значение': {},
                                        'Функция': {}
                                    }
                                },
                                'Правый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Значение': {},
                                        'Функция': {}
                                    }
                                }
                            }
                        }
                    },
                    'Произведение': {
                        'type': 'Функция',
                        'backend_method': '_f_ao_composition',
                        'return_type': ['Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Левый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Значение': {},
                                        'Функция': {}
                                    }
                                },
                                'Правый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Значение': {},
                                        'Функция': {}
                                    }
                                }
                            }
                        }
                    },
                    'Частное': {
                        'type': 'Функция',
                        'backend_method': '_f_ao_quotient',
                        'return_type': ['Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Левый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Значение': {},
                                        'Функция': {}
                                    }
                                },
                                'Правый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Значение': {},
                                        'Функция': {}
                                    }
                                }
                            }
                        }
                    },
                    'Неполное_частное': {
                        'type': 'Функция',
                        'backend_method': '_f_ao_partial_quotient',
                        'return_type': ['Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Левый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Значение': {},
                                        'Функция': {}
                                    }
                                },
                                'Правый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Значение': {},
                                        'Функция': {}
                                    }
                                }
                            }
                        }
                    },
                    'Остаток_частного': {
                        'type': 'Функция',
                        'backend_method': '_f_ao_remainder_quotient',
                        'return_type': ['Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Левый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Значение': {},
                                        'Функция': {}
                                    }
                                },
                                'Правый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Значение': {},
                                        'Функция': {}
                                    }
                                }
                            }
                        }
                    },
                    'Модуль[abs]': {
                        'type': 'Функция',
                        'backend_method': '_f_ao_abs',
                        'return_type': ['Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {}
                                    }
                                }
                            }
                        }
                    },
                    'Округление': {
                        'type': 'Функция',
                        'backend_method': '_f_ao_round',
                        'return_type': ['Таблица', 'Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Таблица': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Таблица': {},
                                        'Функция': {}
                                    }
                                },
                                'Измерения': {
                                    'values': {},
                                    'if_return_type': ['Поле', 'Таблица'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {}
                                    }
                                }
                            }
                        }
                    }
                },
                'Преобразование_типов': {
                    'int64': {
                        'type': 'Функция',
                        'backend_method': '_f_pt_int64',
                        'return_type': ['Таблица', 'Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Таблица': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Таблица': {},
                                        'Функция': {}
                                    }
                                },
                                'Измерения': {
                                    'values': {},
                                    'if_return_type': ['Поле', 'Таблица'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {}
                                    }
                                }
                            }
                        }
                    },
                    'float64': {
                        'type': 'Функция',
                        'backend_method': '_f_pt_float64',
                        'return_type': ['Таблица', 'Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Таблица': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Таблица': {},
                                        'Функция': {}
                                    }
                                },
                                'Измерения': {
                                    'values': {},
                                    'if_return_type': ['Поле', 'Таблица'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {}
                                    }
                                }
                            }
                        }
                    },
                    'datetime64[ns]': {
                        'type': 'Функция',
                        'backend_method': '_f_pt_datetime64',
                        'return_type': ['Таблица', 'Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Таблица': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Таблица': {},
                                        'Функция': {}
                                    }
                                },
                                'Измерения': {
                                    'values': {},
                                    'if_return_type': ['Поле', 'Таблица'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {}
                                    }
                                }
                            }
                        }
                    },
                    'str': {
                        'type': 'Функция',
                        'backend_method': '_f_pt_str',
                        'return_type': ['Таблица', 'Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Таблица': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Таблица': {},
                                        'Функция': {}
                                    }
                                },
                                'Измерения': {
                                    'values': {},
                                    'if_return_type': ['Поле', 'Таблица'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {}
                                    }
                                }
                            }
                        }
                    }
                },
                'Логические_операторы': {
                    'Оператор_И': {
                        'type': 'Функция',
                        'backend_method': '_f_lo_and',
                        'return_type': ['Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Левый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Функция': {}
                                    }
                                },
                                'Правый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Функция': {}
                                    }
                                },
                            }
                        }
                    },
                    'Оператор_ИЛИ': {
                        'type': 'Функция',
                        'backend_method': '_f_lo_or',
                        'return_type': ['Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Левый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Функция': {}
                                    }
                                },
                                'Правый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Функция': {}
                                    }
                                },
                            }
                        }
                    }
                },
                'Операторы_сравнения': {
                    '[ОД]_Оператор_>': {
                        'type': 'Функция',
                        'backend_method': '_f_os_bolshe',
                        'return_type': ['Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Левый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Значение': {},
                                        'Функция': {}
                                    }
                                },
                                'Правый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Значение': {},
                                        'Функция': {}
                                    }
                                }
                            }
                        }
                    },
                    '[ОД]_Оператор_>=': {
                        'type': 'Функция',
                        'backend_method': '_f_os_bolshe_libo_ravno',
                        'return_type': ['Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Левый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Значение': {},
                                        'Функция': {}
                                    }
                                },
                                'Правый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Значение': {},
                                        'Функция': {}
                                    }
                                }
                            }
                        }
                    },
                    '[ОД]_Оператор_<': {
                        'type': 'Функция',
                        'backend_method': '_f_os_menshe',
                        'return_type': ['Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Левый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Значение': {},
                                        'Функция': {}
                                    }
                                },
                                'Правый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Значение': {},
                                        'Функция': {}
                                    }
                                }
                            }
                        }
                    },
                    '[ОД]_Оператор_<=': {
                        'type': 'Функция',
                        'backend_method': '_f_os_menshe_libo_ravno',
                        'return_type': ['Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Левый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Значение': {},
                                        'Функция': {}
                                    }
                                },
                                'Правый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Значение': {},
                                        'Функция': {}
                                    }
                                }
                            }
                        }
                    },
                    '[ОД]_Оператор_==': {
                        'type': 'Функция',
                        'backend_method': '_f_os_ravno',
                        'return_type': ['Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Левый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Значение': {},
                                        'Функция': {}
                                    }
                                },
                                'Правый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Значение': {},
                                        'Функция': {}
                                    }
                                }
                            }
                        }
                    },
                    '[ОД]_Оператор_!=': {
                        'type': 'Функция',
                        'backend_method': '_f_os_ne_ravno',
                        'return_type': ['Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Левый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Значение': {},
                                        'Функция': {}
                                    }
                                },
                                'Правый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Значение': {},
                                        'Функция': {}
                                    }
                                }
                            }
                        }
                    },
                    '[ОД]_Промежуток': {
                        'type': 'Функция',
                        'backend_method': '_f_os_between',
                        'return_type': ['Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {}
                                    }
                                },
                                'Начало': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Значение': {}
                                    }
                                },
                                'Конец': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Значение': {}
                                    }
                                }
                            }
                        }
                    },
                    'Оператор_>': {
                        'type': 'Функция',
                        'backend_method': '_f_os_bolshe',
                        'return_type': ['Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Левый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {},
                                        'Значение': {}
                                    }
                                },
                                'Правый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {},
                                        'Значение': {}
                                    }
                                },
                                'Если_верно': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {},
                                        'Значение': {}
                                    }
                                },
                                'Если_ложно': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {},
                                        'Значение': {}
                                    }
                                }
                            }
                        }
                    },
                    'Оператор_>=': {
                        'type': 'Функция',
                        'backend_method': '_f_os_bolshe_libo_ravno',
                        'return_type': ['Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Левый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {},
                                        'Значение': {}
                                    }
                                },
                                'Правый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {},
                                        'Значение': {}
                                    }
                                },
                                'Если_верно': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {},
                                        'Значение': {}
                                    }
                                },
                                'Если_ложно': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {},
                                        'Значение': {}
                                    }
                                }
                            }
                        }
                    },
                    'Оператор_<': {
                        'type': 'Функция',
                        'backend_method': '_f_os_menshe',
                        'return_type': ['Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Левый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {},
                                        'Значение': {}
                                    }
                                },
                                'Правый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {},
                                        'Значение': {}
                                    }
                                },
                                'Если_верно': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {},
                                        'Значение': {}
                                    }
                                },
                                'Если_ложно': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {},
                                        'Значение': {}
                                    }
                                }
                            }
                        }
                    },
                    'Оператор_<=': {
                        'type': 'Функция',
                        'backend_method': '_f_os_menshe_libo_ravno',
                        'return_type': ['Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Левый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {},
                                        'Значение': {}
                                    }
                                },
                                'Правый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {},
                                        'Значение': {}
                                    }
                                },
                                'Если_верно': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {},
                                        'Значение': {}
                                    }
                                },
                                'Если_ложно': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {},
                                        'Значение': {}
                                    }
                                }
                            }
                        }
                    },
                    'Оператор_==': {
                        'type': 'Функция',
                        'backend_method': '_f_os_ravno',
                        'return_type': ['Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Левый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {},
                                        'Значение': {}
                                    }
                                },
                                'Правый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {},
                                        'Значение': {}
                                    }
                                },
                                'Если_верно': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {},
                                        'Значение': {}
                                    }
                                },
                                'Если_ложно': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {},
                                        'Значение': {}
                                    }
                                }
                            }
                        }
                    },
                    'Оператор_!=': {
                        'type': 'Функция',
                        'backend_method': '_f_os_ne_ravno',
                        'return_type': ['Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Левый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {},
                                        'Значение': {}
                                    }
                                },
                                'Правый_операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {},
                                        'Значение': {}
                                    }
                                },
                                'Если_верно': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {},
                                        'Значение': {}
                                    }
                                },
                                'Если_ложно': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {},
                                        'Значение': {}
                                    }
                                }
                            }
                        }
                    },
                    'Промежуток': {
                        'type': 'Функция',
                        'backend_method': '_f_os_between',
                        'return_type': ['Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Операнд': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {}
                                    }
                                },
                                'Начало': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Значение': {}
                                    }
                                },
                                'Конец': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Значение': {}
                                    }
                                },
                                'Если_верно': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {},
                                        'Значение': {}
                                    }
                                },
                                'Если_ложно': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {},
                                        'Значение': {}
                                    }
                                }
                            }
                        }
                    }
                },
                'Реляционная_алгебра': {
                    'Соединение': {
                        'type': 'Функция',
                        'backend_method': '_f_ra_concatenation',
                        'return_type': ['Таблица'],
                        'tree_struct': {
                            'Параметры': {
                                'Таблица_1': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Таблица': {},
                                        'Функция': {}
                                    }
                                },
                                'Таблица_2': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Таблица': {},
                                        'Функция': {}
                                    }
                                },
                                'Объединить_по_столбцу_слева': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Поле': {}
                                    }
                                },
                                'Объединить_по_столбцу_справа': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Поле': {}
                                    }
                                },
                                'Результирующие_поля': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Поле': {},
                                    }
                                }
                            }
                        }
                    },
                    'Соединение[LEFT]': {
                        'type': 'Функция',
                        'backend_method': '_f_ra_concatenation_left',
                        'return_type': ['Таблица'],
                        'tree_struct': {
                            'Параметры': {
                                'Таблица_1': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Таблица': {},
                                        'Функция': {}
                                    }
                                },
                                'Таблица_2': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Таблица': {},
                                        'Функция': {}
                                    }
                                },
                                'Объединить_по_столбцу_слева': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Поле': {}
                                    }
                                },
                                'Объединить_по_столбцу_справа': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Поле': {}
                                    }
                                },
                                'Результирующие_поля': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Поле': {},
                                    }
                                }
                            }
                        }
                    },
                    'Соединение[RIGHT]': {
                        'type': 'Функция',
                        'backend_method': '_f_ra_concatenation_right',
                        'return_type': ['Таблица'],
                        'tree_struct': {
                            'Параметры': {
                                'Таблица_1': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Таблица': {},
                                        'Функция': {}
                                    }
                                },
                                'Таблица_2': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Таблица': {},
                                        'Функция': {}
                                    }
                                },
                                'Объединить_по_столбцу_слева': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Поле': {}
                                    }
                                },
                                'Объединить_по_столбцу_справа': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Поле': {}
                                    }
                                },
                                'Результирующие_поля': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Поле': {},
                                    }
                                }
                            }
                        }
                    },
                    'Соединение[OUTER]': {
                        'type': 'Функция',
                        'backend_method': '_f_ra_concatenation_outer',
                        'return_type': ['Таблица'],
                        'tree_struct': {
                            'Параметры': {
                                'Таблица_1': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Таблица': {},
                                        'Функция': {}
                                    }
                                },
                                'Таблица_2': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Таблица': {},
                                        'Функция': {}
                                    }
                                },
                                'Объединить_по_столбцу_слева': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Поле': {}
                                    }
                                },
                                'Объединить_по_столбцу_справа': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Поле': {}
                                    }
                                },
                                'Результирующие_поля': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Поле': {},
                                    }
                                }
                            }
                        }
                    },
                    'Объединение': {
                        'type': 'Функция',
                        'backend_method': '_f_ra_union',
                        'return_type': ['Таблица'],
                        'tree_struct': {
                            'Параметры': {
                                'Таблица_1': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Таблица': {},
                                        'Функция': {}
                                    }
                                },
                                'Таблица_2': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Таблица': {},
                                        'Функция': {}
                                    }
                                },
                                'Объединить_по_столбцу_слева': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Поле': {}
                                    }
                                },
                                'Объединить_по_столбцу_справа': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Поле': {}
                                    }
                                },
                                'Результирующие_поля': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Поле': {},
                                    }
                                }
                            }
                        }
                    },
                    'Отбор_данных': {
                        'type': 'Функция',
                        'backend_method': '_f_ra_data_selection',
                        'return_type': ['Таблица'],
                        'tree_struct': {
                            'Параметры': {
                                'Таблица': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Таблица': {},
                                        'Функция': {}
                                    }
                                },
                                'Функция_сравнения': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Функция': {},
                                    }
                                },
                                'Результирующие_поля': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Поле': {},
                                    }
                                }
                            }
                        }
                    },
                    'Сортировка_восходящая': {
                        'type': 'Функция',
                        'backend_method': '_f_ra_sort_increase',
                        'return_type': ['Поле', 'Таблица'],
                        'tree_struct': {
                            'Параметры': {
                                'Таблица': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Таблица': {},
                                        'Функция': {}
                                    }
                                },
                                'Измерения': {
                                    'values': {},
                                    'if_return_type': ['Поле', 'Таблица'],
                                    '__possible_values__': {
                                        'Поле': {}
                                    }
                                }
                            }
                        }
                    },
                    'Сортировка_нисходящая': {
                        'type': 'Функция',
                        'backend_method': '_f_ra_sort_decrease',
                        'return_type': ['Поле', 'Таблица'],
                        'tree_struct': {
                            'Параметры': {
                                'Таблица': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Таблица': {},
                                        'Функция': {}
                                    }
                                },
                                'Измерения': {
                                    'values': {},
                                    'if_return_type': ['Поле', 'Таблица'],
                                    '__possible_values__': {
                                        'Поле': {}
                                    }
                                }
                            }
                        }
                    },
                    'Копия': {
                        'type': 'Функция',
                        'backend_method': '_f_ra_copy',
                        'return_type': ['Таблица', 'Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Таблица': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Таблица': {},
                                        'Функция': {}
                                    }
                                },
                                'Поле': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {}
                                    }
                                },
                                'Результирующие_поля': {
                                    'values': {},
                                    'if_return_type': ['Таблица'],
                                    '__possible_values__': {
                                        'Поле': {},
                                    }
                                }
                            }
                        }
                    }
                },
                'Работа_с_датой': {
                    'Начало_дня': {
                        'type': 'Функция',
                        'backend_method': '_f_rsd_start_day',
                        'return_type': ['Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Измерение': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {}
                                    }
                                }
                            }
                        }
                    },
                    'Начало_недели': {
                        'type': 'Функция',
                        'backend_method': '_f_rsd_start_week',
                        'return_type': ['Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Измерение': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {}
                                    }
                                }
                            }
                        }
                    },
                    'Начало_месяца': {
                        'type': 'Функция',
                        'backend_method': '_f_rsd_start_month',
                        'return_type': ['Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Измерение': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {}
                                    }
                                }
                            }
                        }
                    },
                    'Начало_года': {
                        'type': 'Функция',
                        'backend_method': '_f_rsd_start_year',
                        'return_type': ['Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Измерение': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {}
                                    }
                                }
                            }
                        }
                    },
                    'Сбор_даты_и_времени': {
                        'type': 'Функция',
                        'backend_method': '_f_rsd_set_datetime_from_parts',
                        'return_type': ['Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Год': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {},
                                        'Значение': {}
                                    }
                                },
                                'Месяц': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {},
                                        'Значение': {}
                                    }
                                },
                                'День': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {},
                                        'Значение': {}
                                    }
                                },
                                'Час': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {},
                                        'Значение': {}
                                    }
                                },
                                'Минута': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {},
                                        'Значение': {}
                                    }
                                },
                                'Секунда': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {},
                                        'Значение': {}
                                    }
                                }
                            }
                        }
                    },
                    'Сбор_даты': {
                        'type': 'Функция',
                        'backend_method': '_f_rsd_set_date_from_parts',
                        'return_type': ['Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Год': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {},
                                        'Значение': {}
                                    }
                                },
                                'Месяц': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {},
                                        'Значение': {}
                                    }
                                },
                                'День': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {},
                                        'Значение': {}
                                    }
                                }
                            }
                        }
                    },
                    'Получить_Год': {
                        'type': 'Функция',
                        'backend_method': '_f_rsd_get_year_from_date',
                        'return_type': ['Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Измерение': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {}
                                    }
                                },
                            }
                        }
                    },
                    'Получить_Месяц': {
                        'type': 'Функция',
                        'backend_method': '_f_rsd_get_month_from_date',
                        'return_type': ['Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Измерение': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {}
                                    }
                                },
                            }
                        }
                    },
                    'Получить_День': {
                        'type': 'Функция',
                        'backend_method': '_f_rsd_get_day_from_date',
                        'return_type': ['Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Измерение': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {}
                                    }
                                },
                            }
                        }
                    },
                    'Получить_Час': {
                        'type': 'Функция',
                        'backend_method': '_f_rsd_get_hour_from_date',
                        'return_type': ['Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Измерение': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {}
                                    }
                                },
                            }
                        }
                    },
                    'Получить_Минуту': {
                        'type': 'Функция',
                        'backend_method': '_f_rsd_get_minute_from_date',
                        'return_type': ['Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Измерение': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {}
                                    }
                                },
                            }
                        }
                    },
                    'Получить_Секунду': {
                        'type': 'Функция',
                        'backend_method': '_f_rsd_get_second_from_date',
                        'return_type': ['Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Измерение': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Поле': {},
                                        'Функция': {}
                                    }
                                },
                            }
                        }
                    }
                },
                'Прочее': {
                    'Значение': {
                        'type': 'Функция',
                        'backend_method': '_f_pr_value',
                        'return_type': ['Поле'],
                        'tree_struct': {
                            'Параметры': {
                                'Значение': {
                                    'values': {},
                                    'if_return_type': ['Поле'],
                                    '__possible_values__': {
                                        'Значение': {}
                                    }
                                }
                            }
                        }
                    },
                    'NaN': {
                        'type': 'Функция',
                        'backend_method': '_f_pr_nan',
                        'return_type': ['Поле'],
                        'tree_struct': {
                            'Параметры': {}
                        }
                    }
                }
            }
        }

    def _save_operands(self, operands: dict):
        if operands:
            self.operands = operands
            self.bk_object.properties['operands']['value'] = operands
            self.bk_object.update_object()
        return self.operands

    def _filter_runtime_fields(self, fields_operands: dict):
        for fld, fld_opt in fields_operands.items():
            if fld_opt['type'] == 'Функция':
                if fld_opt.get('backend_method') != '_f_pr_nan':
                    self.table_df.drop(fld, axis=1, inplace=True)

    def set_tbl_to_mapper(self, source_tbl_name, current_tbl_name, source_columns, current_columns):
        if self.operands['main_mapper'].get(source_tbl_name) is None:
            self.operands['main_mapper'][source_tbl_name] = {
                'source_self_name': source_tbl_name,
                'current_self_name': current_tbl_name
            }
        self.set_fields_to_mapper(source_tbl_name, source_columns, current_columns)

    def set_fields_to_mapper(self, source_tbl_name, source_columns, current_columns):
        fields = self.operands['main_mapper'][source_tbl_name].get('fields')
        if fields is None:
            fields = {}
        columns = dict(zip(source_columns, current_columns))
        for src, curr in columns.items():
            if fields.get(src) is None:
                fields.setdefault(src, {}).setdefault('source_self_name', src)
                fields.setdefault(src, {}).setdefault('current_self_name', curr)
        self.operands['main_mapper'][source_tbl_name]['fields'] = fields

    def _init_adf_table(self, data_dct, tbl):
        source_columns = data_dct['columns']
        data = data_dct['data']

        if data_dct.get('operands'):
            source_tbl_name = data_dct['operands']['tables'][tbl]['display_name']
            current_tbl_name = source_tbl_name.replace(' ', '_')
        else:
            source_tbl_name = tbl
            tbl_bk_object = BackendCObject.init_from_mongo(tbl)
            current_tbl_name = tbl_bk_object.display_name
        current_columns = [self.new_name(col.replace(' ', '_'), self.columns_id) for col in source_columns]
        for col in current_columns:
            self.columns_id[col] = col
        self.tables[source_tbl_name] = pd.DataFrame(data, columns=source_columns).replace('NaN', np.nan)

        self.set_tbl_to_mapper(source_tbl_name, current_tbl_name, source_columns, current_columns)

    def _init_tables(self, previous: list = None):
        self.columns_id = {}
        try:
            if isinstance(previous, dict):
                self._init_adf_table(previous, previous['table_name'])
            else:
                for tbl_item in previous:
                    self._init_adf_table(tbl_item, tbl_item['table_name'])
        except Exception:
            MessageError('DataFrame', 'Не удалось загрузить таблицу')
            return

    def _transform_to_datetime(self):
        for tbl_name, table in self.tables.items():
            if not self._date_cols.get(tbl_name):
                self._date_cols[tbl_name] = list()

            if isinstance(table, pd.DataFrame):
                for col in table.columns:
                    try:
                        _is_date, _dt_format = self._is_date_format(table[col][0])
                        if _is_date:
                            try:
                                table[col] = pd.to_datetime(table[col], format=_dt_format)
                                if col not in self._date_cols[tbl_name]:
                                    self._date_cols[tbl_name].append(col)
                            except ValueError:
                                pass
                        if table[col].dtype in ['datetime64[ns]', 'timedelta64[ns]']:
                            if col not in self._date_cols[tbl_name]:
                                self._date_cols[tbl_name].append(col)
                    except KeyError:
                        continue

    def _transform_from_datetime(self):
        for tbl_name, cols in self._date_cols.items():
            for col in cols:
                if col in list(self.tables[tbl_name].columns):
                    try:
                        self.tables[tbl_name][col] = self.tables[tbl_name][col].dt.strftime('%Y-%m-%d %H:%M:%S')
                    except AttributeError:
                        continue

    @staticmethod
    def new_name(new_name: str, chk_dct: dict, i=0):
        if new_name is None or new_name == '':
            new_name = 'New_element'
        new_name_n = new_name if i == 0 else new_name + '_' + str(i)
        if chk_dct.get(new_name_n) is not None:
            return AdvancedDataFrame.new_name(new_name, chk_dct, i + 1)
        else:
            return new_name_n

    @staticmethod
    def _is_date_format(string):
        formats_dt = [
            '%Y-%m-%d %H:%M:%S', '%d-%m-%Y %H:%M:%S',
            '%Y/%m/%d %H:%M:%S', '%d/%m/%Y %H:%M:%S',
            '%Y.%m.%d %H:%M:%S', '%d.%m.%Y %H:%M:%S',
            '%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d',
            '%d/%m/%Y', '%Y.%m.%d', '%d.%m.%Y'
        ]

        r = False
        _f = None
        for f in formats_dt:
            try:
                r = datetime.datetime.strptime(string, f)
            except Exception:
                continue
            else:
                _f = f
                break
        return (True, _f) if r else (False, None)

    @staticmethod
    def _get_path(tmp, suffix=False):
        _tmp = os.path.join(config.TOPOS_TEMP, tmp)

        if suffix:
            return _tmp + '.feather'
        return _tmp

    @staticmethod
    def _get_unq_filename(path=False, suffix=False):
        while True:
            tmp = next(tempfile._get_candidate_names())
            if not os.path.isfile(AdvancedDataFrame._get_path(tmp + '.feather')):
                if path:
                    if suffix:
                        return AdvancedDataFrame._get_path(tmp + '.feather')
                    return AdvancedDataFrame._get_path(tmp)
                return tmp


if __name__ == '__main__':
    pass
