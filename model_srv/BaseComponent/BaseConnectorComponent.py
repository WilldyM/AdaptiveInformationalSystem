from model_srv.BaseComponent.BaseComponent import BaseComponent


class BaseConnectorComponent(BaseComponent):
    """
    BaseConnectorComponent содержит стандартные настройки для категорий типа "коннектор".
    """

    def load_tbl(self, tbl, table_name, field_map):
        pass

    def build_queries(self, _q_data):
        pass

    def extract_all(self, model_form):
        pass

    def get_metadata(self, model_form):
        return None
