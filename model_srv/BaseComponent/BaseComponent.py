class BaseComponent(object):
    """
    BaseComponent содержит стандартные настройки, которые должны содержать все категории.
    """

    @staticmethod
    def get_export_data(md_obj):
        return None

    @staticmethod
    def non_default_properties_processing(md_obj, method):
        return False

    @staticmethod
    def specified_possible_out_values(el_obj, opv):
        return opv
