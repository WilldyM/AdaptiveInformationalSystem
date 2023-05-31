import sys

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from desktop_version.pyside6.auth_form.ui_auth_form import Ui_AuthForm
from desktop_version.pyside6.messages.messagebox import MessageError, MessageInfo

from model_srv.mongodb.auth.AuthService import MongoAuthService


class AuthForm(QWidget, Ui_AuthForm):
    user = None
    mongo_conn = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        self.setLayout(self.verticalLayout)
        self.resize(200, 90)

        # lineEdit options
        self.lineEdit.setPlaceholderText('Логин')
        self.lineEdit_2.setPlaceholderText('Пароль')
        self.lineEdit_2.setEchoMode(QLineEdit.Password)

        # connects
        self.authButton.clicked.connect(self.check_auth_data)
        self.registerButton.clicked.connect(self.check_register_data)

    def resize_to_default(self):
        self.resize(200, 90)

    def check_auth_data(self):
        self.mongo_conn = MongoAuthService()
        login = self.lineEdit.text()
        password = self.lineEdit_2.text()
        print('auth')
        try:
            self.user = self.mongo_conn.auth(login, password)
        except ValueError as err:
            text_error = 'Error: ' + err.args[0]
            MessageError(title='Ошибка при авторизации', text=text_error)

        self.mongo_conn.close_connection()

    def check_register_data(self):
        self.mongo_conn = MongoAuthService()
        login = self.lineEdit.text()
        password = self.lineEdit_2.text()
        print('register')

        msg_title = 'Регистрация'
        try:
            self.user = self.mongo_conn.register(login, password)
        except ValueError as err:
            msg_text = 'Error: ' + err.args[0]
            MessageError(title=msg_title, text=msg_text)
        else:
            msg_text = f'Пользователь {login} был успешно создан!'
            MessageInfo(title=msg_title, text=msg_text)
        self.mongo_conn.close_connection()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    form = AuthForm()
    form.show()
    app.exec()

