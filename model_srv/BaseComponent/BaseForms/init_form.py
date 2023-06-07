import json
from functools import partial

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

from model_srv.mongodb.ModelService import BackendModel


class InitForm(QDialog):
    def __init__(self, parent_widget, main_object, *args, **kwargs):
        super().__init__(parent_widget, *args, **kwargs)
        self.main_object = main_object
        self.edit_props = list()
        self.setup_ui()

    def setup_ui(self):
        self.default_width = 400
        self.default_height = 30

        self.setLayout(QVBoxLayout())
        self.create_pattern_properties()
        self.button_ok = QPushButton('Ок')
        self.button_ok.clicked.connect(self.save_properties)
        self.button_close = QPushButton('Отмена')
        self.button_close.clicked.connect(self.close)

        horizontal_layout = QHBoxLayout()
        horizontal_layout.insertWidget(0, self.button_ok)
        horizontal_layout.insertWidget(1, self.button_close)

        self.layout().addLayout(horizontal_layout)

        self.resize(self.default_width, self.default_height)

    def save_properties(self):
        for edit_prop in self.edit_props:
            if isinstance(edit_prop, QLineEdit):
                self.main_object.bk_object.properties[edit_prop._id]['value'] = edit_prop.text()
            elif isinstance(edit_prop, QComboBox):
                self.main_object.bk_object.properties[edit_prop._id]['value'] = edit_prop.currentText()
        self.main_object.bk_object.update_object()
        bk_model = BackendModel.init_from_mongo(self.parent().active_model)
        self.parent().update_model(bk_model)
        self.close()

    @staticmethod
    def select_file(parent, edit_prop, file_types: list):
        """
        Вызывает диалог выбора файла и сохраняет выбранный путь в свойстве file_path.
        :return: Путь к выбранному файлу
        """
        if not file_types:
            _file_types = 'Файлы (*.*)'
        else:
            _file_types = ';;'.join([f'File ({file})' for file in file_types])
        file_path = QFileDialog.getOpenFileName(parent, "Выбрать файл", "", _file_types)[0]
        if file_path:
            edit_prop.setText(file_path)
        else:
            return

    def create_pattern_properties(self):
        properties = self.main_object.bk_object.properties
        horizontal_layout = QHBoxLayout()
        labels_vertical_layout = QVBoxLayout()
        edit_vertical_layout = QVBoxLayout()
        horizontal_layout.insertLayout(0, labels_vertical_layout)
        horizontal_layout.insertLayout(1, edit_vertical_layout)
        self.layout().addLayout(horizontal_layout)
        for prop in properties.values():
            label_prop = QLabel()
            label_prop.setText(prop['display_name'])
            possible_values = self.main_object.get_possible_values(prop['self_name'])
            if possible_values:
                edit_prop = QComboBox()
                edit_prop.addItems(possible_values)
                if prop['value']:
                    edit_prop.setCurrentText(prop['value'])
            else:
                edit_prop = QLineEdit()
                edit_prop.setPlaceholderText('Введите значение')
                if prop['value']:
                    if isinstance(prop['value'], (dict, list)):
                        edit_prop.setText(json.dumps(prop['value']))
                    else:
                        edit_prop.setText(str(prop['value']))

            certain_layout = None
            if prop['certain']:
                if prop['certain'].split(' ')[0] == 'file':
                    edit_prop.setPlaceholderText('Выберите файл')
                    certain_layout = QHBoxLayout()
                    fileButton = QPushButton('...')
                    file_types = json.loads(prop['certain'].split(' ')[1])
                    fileButton.clicked.connect(partial(self.select_file, self, edit_prop, file_types))
                    fileButton.setFixedWidth(30)
                    certain_layout.insertWidget(0, edit_prop)
                    certain_layout.insertWidget(1, fileButton)

            edit_prop._id = prop['self_name']
            self.edit_props.append(edit_prop)

            labels_vertical_layout.addWidget(label_prop)
            if certain_layout:
                edit_vertical_layout.addLayout(certain_layout)
            else:
                edit_vertical_layout.addWidget(edit_prop)

            self.default_height += 15