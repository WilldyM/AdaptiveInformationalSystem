from model_srv.BaseComponent.BaseComponent import BaseComponent


class BaseConnectorComponent(BaseComponent):
    """
    BaseConnectorComponent содержит стандартные настройки для категорий типа "коннектор".
    """

    def load_tbl(self, tbl, table_name, field_map):
        pass

    def build_queries(self, _q_data, preview_rows=0):
        pass

    def extract_all(self, dont_change_answer=False):
        pass

    def get_metadata(self):
        return None
