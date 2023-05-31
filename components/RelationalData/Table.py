import mcore_root.ModelCore as MC
from model_srv.md_el_obj import MDObject
import pandas as pd
import json
import numpy as np
from model_srv.BaseComponent.BaseDataComponent import BaseDataComponent
from model_srv.TMPFile import TMPFile


class RlTable(BaseDataComponent):
    def __init__(self, fields: list, data_space: MC.Model):
        self.fields = fields
        self.data_space = data_space

    @staticmethod
    def get_data(mdobj, load_relational_data=True):
        if load_relational_data:
            # r = mdobj.run({}, 'show_table')['show_table']
            # mdobj.res = None
            r = RlTable.show_table(mdobj.self_name, mdobj.metamodel)
        else:
            # data = mdobj.run({}, 'show_table')['show_table']
            # mdobj.res = None
            data = RlTable.show_table(mdobj.self_name, mdobj.metamodel)
            r = {'fields': data['columns']}
        return r

    @staticmethod
    def show_table(table_name, metamodel):
        data_space = metamodel.objects[table_name].properties['data_space']
        ds_obj = metamodel.dt_spaces[data_space]
        fields_mdobject = list(metamodel.objects[table_name].properties['fields'].keys())
        fields = [f for f in fields_mdobject if ds_obj.values.get(f) is not None]
        if len(fields) != len(fields_mdobject):
            metamodel.objects[table_name].properties['fields'] = {f: f for f in fields}
        try:
            r = ds_obj.asc_list_as_table(ds_obj.values[table_name].asc_lst, fields)
            ret_df = pd.DataFrame(r)
            r = json.loads(ret_df.replace(np.nan, 'NaN').to_json(orient='split'))
            r.pop('index')
        except KeyError:
            r = {'data': [], 'columns': []}
        return r


    @staticmethod
    def to_clear_table_data(_mdo: MDObject):
        ds_name = _mdo.properties['data_space']
        ds_obj = _mdo.metamodel.dt_spaces[ds_name]
        d_obj = ds_obj.values.get(_mdo.self_name)
        cleared_asc_dct = d_obj.clear_asc()

        ds_obj.data_objects[d_obj.obj_id] = None
        ds_obj.empty_places.append(d_obj.obj_id)
        ds_obj.values.pop(d_obj.obj_value, None)

        for asc_name, asc_obj in cleared_asc_dct.items():
            if asc_obj.associations == {}:
                ds_obj.data_objects[asc_obj.obj_id] = None
                ds_obj.values.pop(asc_name, None)
            else:
                asc_obj_lst = dict(asc_obj.associations)
                asc_obj_lst.update(dict(asc_obj.objects))
                asc_obj_lst = list(asc_obj_lst.keys())
                ds_obj.values[ds_obj._get_asc_value(asc_obj_lst)] = asc_obj
                del ds_obj.values[asc_name]
        # ds_obj.relational_delete_table(_mdo.self_name)
        return True
