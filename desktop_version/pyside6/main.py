import sys

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from desktop_version.pyside6.auth_form.auth_form import AuthForm

from model_srv.mongodb.auth.AuthService import MongoAuthService


class MainWindow(QMainWindow):
    mongo_conn = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resize(800, 600)
        self.centralwidget = QWidget(self)
        self.setCentralWidget(self.centralwidget)
        self.setWindowTitle('AdaptiveIS.Авторизация')

        # добавили виджет для авторизации
        self.auth_widget = AuthForm(self.centralwidget)
        self.centerWidget(self, self.auth_widget)

    @staticmethod
    def centerWidget(center_from, center_what):
        center_what.move((center_from.width() - center_what.width()) / 2,
                         (center_from.height() - center_what.height()) / 2)

    def resizeEvent(self, event):
        new_width, new_height = event.size().toTuple()
        self.auth_widget.move((new_width - self.auth_widget.width()) / 2,
                              (new_height - self.auth_widget.height()) / 2)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    form = MainWindow()
    form.show()
    app.exec()

