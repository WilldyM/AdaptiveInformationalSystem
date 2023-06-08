import sys

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from desktop_version.pyside6.auth_form.auth_form import AuthForm
from desktop_version.pyside6.custom_items.CustomAnimation import ArcWidget
from desktop_version.pyside6.custom_items.CustomTreeWidgetItem import CustomTreeWidgetItem
from desktop_version.pyside6.model_form.model_form import ModelForm

from model_srv.mongodb.auth.AuthService import MongoAuthService
from utils.startup_updates import init_categories_to_db, init_template_of_dirs, try_to_create_superuser


gray_styles = '''

QMenuBar {
    background-color: #E6E6E6;
    color: #000;
    font-weight: bold;
}

QMenuBar::item {
    background-color: #E6E6E6;
    color: #000;
    padding: 8px 14px;
    spacing: 6px;
}

QMenuBar::item:selected {
    background-color: #9B9B9B;
    color: #FFFFFF;
}

QMenu {
    background-color: #F4F4F4;
    color: #404040;
    border: 1px solid #9B9B9B;
    padding: 0px;
}

QMenu::item {
    padding: 6px 20px;
    border-bottom: 1px solid #9B9B9B;
}

QMenu::item:selected {
    background-color: #9B9B9B;
    color: #FFFFFF;
}

QLineEdit {
    background-color: #F4F4F4;
    color: #404040;
    border: 1px solid #ccc;
    padding: 1px 5px;
    border-radius: 4px;
    min-height: 25px;
}

QLineEdit:hover, QLineEdit:focus {
    background-color: #FFFFFF;
    border: 1px solid #9B9B9B;
}

QLabel {
    color: #444444;
}

QWidget:focus {
    outline: none;
}

QPushButton {
background-color: rgba(255, 255, 255, 20%); 
border: 1px solid #ccc;
border-radius: 4px;
padding: 2px 15px;
max-height: 30px;
margin-top: 2px;
margin-bottom: 4px;
min-height: 30px;
}

QPushButton:hover {
    background-color: rgba(255, 255, 255, 80%);
}
QPushButton:pressed {
    background-color: rgba(255, 255, 255, 100%);
}

QLabel {
    color: #808080; /* серый цвет текста */
}

QTreeWidget::item {
    color: #555;
    padding: 5px 0px;
}
QTreeWidget::item:hover {
    background: #f3f3f3;
    padding: 5px 0px;
}

QTreeWidget::item:selected {
    background: #f3f3f3;
}

QTreeWidget {
    background-color: #fff;
    border-style: outset;
    border-width: 1px;
    border-color: #ccc;
    font: 12px;
    padding: 6px;
}

QListWidget {
    background-color: #fff;
    border-style: outset;
    border-width: 1px;
    border-color: #ccc;
    font: 12px;
    padding: 6px;
}

QHeaderView::section {
    background-color: #fff;
    color: #555;
    font: bold 14px;
    border: none;
    padding: 3px;
    text-align: center;
}

QScrollBar { background-color: #d9d9d9; width: 10px; }

QScrollBar::handle { background-color: #b3b3b3; }

QScrollBar::add-page, QScrollBar::sub-page { background-color: none; }

QScrollBar::add-line, QScrollBar::sub-line { border: none; background: none; }

QScrollBar:horizontal { height: 10px; color: #333; }

QScrollBar::handle:horizontal { background-color: #b3b3b3; min-width: 30px; }

QScrollBar::add-line:horizontal { border-right: 1px solid #999; background-color: none; width: 20px; subcontrol-position: right; }

QScrollBar::sub-line:horizontal { border-left: 1px solid #999; background-color: none; width: 20px; subcontrol-position: left; }

QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { width: 20px; background: none; }

QScrollBar:vertical { width: 10px; color: #333; }

QScrollBar::handle:vertical { background-color: #b3b3b3; min-height: 30px; }

QScrollBar::add-line:vertical { border-bottom: 1px solid #999; background-color: none; height: 20px; subcontrol-position: bottom; }

QScrollBar::sub-line:vertical { border-top: 1px solid #999; background-color: none; height: 20px; subcontrol-position: top; }

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { height: 20px; background: none; }

QScrollBar::sub-line:vertical {
    border-top: 1px solid #999;
    background-color: none;
    height: 20px;
    subcontrol-position: top;
    margin-top: 1px; /* добавляем отступ в 1px */
}

QScrollBar::add-line:vertical {
    border-bottom: 1px solid #999;
    background-color: none;
    height: 20px;
    subcontrol-position: bottom;
    margin-bottom: 1px; /* добавляем отступ в 1px */
}

QScrollBar:vertical {
    width: 10px;
    color: #333;
}

QScrollBar::handle:vertical {
    background-color: #b3b3b3;
    min-height: 30px;
}

QScrollBar::add-line:vertical {
    border-bottom: 1px solid #999;
    background-color: none;
    height: 20px;
    subcontrol-position: bottom;
    margin-bottom: 1px;
}

QScrollBar::sub-line:vertical {
    border-top: 1px solid #999;
    background-color: none;
    height: 20px;
    subcontrol-position: top;
    margin-top: 1px;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    height: 20px;
    background: none;
}

QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
    width: 20px;
    height: 20px;
    background-color: none;
    image: none;
}

QScrollBar::up-arrow:vertical {
    subcontrol-position: top;
    border-top: 1px solid #999;
}

QScrollBar::down-arrow:vertical {
    subcontrol-position: bottom;
    border-bottom: 1px solid #999;
}

QScrollBar::handle:vertical:hover, QScrollBar::add-line:vertical:hover, QScrollBar::sub-line:vertical:hover {
    background-color: #8c8c8c;
}

QScrollBar::add-line:vertical:pressed, QScrollBar::sub-line:vertical:pressed {
    background-color: #bfbfbf;
}

QScrollBar::handle:vertical:pressed {
    background-color: #8c8c8c;
}
'''


class MainWindow(QMainWindow):
    mongo_conn = None
    user = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resize(800, 600)
        self.centralwidget = QWidget(self)
        self.setCentralWidget(self.centralwidget)
        self.setWindowTitle('AdaptiveIS.Авторизация')
        self.setStyleSheet(gray_styles)

        # добавили виджет для авторизации
        self.auth_widget = AuthForm(parent=self.centralwidget, auth_signal=self.auth_callback)
        self.centerWidget(self, self.auth_widget)

    @Slot()
    def auth_callback(self):
        print('authenticated!')
        self.user = self.auth_widget.user
        self.auth_widget.setHidden(True)
        self.auth_widget = None

        self.centralwidget = ModelForm(self)
        self.centralwidget.user = self.user
        self.setCentralWidget(self.centralwidget)
        self.setWindowTitle('AdaptiveIS.ModelManagement')

    @staticmethod
    def centerWidget(center_from, center_what):
        center_what.move((center_from.width() - center_what.width()) / 2,
                         (center_from.height() - center_what.height()) / 2)

    def resizeEvent(self, event):
        if self.auth_widget is None:
            return
        new_width, new_height = event.size().toTuple()
        self.auth_widget.move((new_width - self.auth_widget.width()) / 2,
                              (new_height - self.auth_widget.height()) / 2)


def on_start_up():
    try_to_create_superuser()
    init_template_of_dirs()
    init_categories_to_db()


if __name__ == '__main__':
    on_start_up()

    app = QApplication(sys.argv)
    form = MainWindow()
    form.show()
    sys.exit(app.exec())

