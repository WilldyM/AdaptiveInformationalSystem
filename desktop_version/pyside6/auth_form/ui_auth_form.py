# -*- coding: utf-8 -*-

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
                            QMetaObject, QObject, QPoint, QRect,
                            QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
                           QFont, QFontDatabase, QGradient, QIcon,
                           QImage, QKeySequence, QLinearGradient, QPainter,
                           QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLineEdit, QPushButton,
                               QSizePolicy, QVBoxLayout, QWidget)


class Ui_AuthForm(object):
    def setupUi(self, AuthForm):
        if not AuthForm.objectName():
            AuthForm.setObjectName(u"AuthForm")
        AuthForm.resize(400, 300)
        self.verticalLayoutWidget = QWidget(AuthForm)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayoutWidget.setGeometry(QRect(80, 80, 221, 91))
        self.verticalLayout = QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.lineEdit = QLineEdit(self.verticalLayoutWidget)
        self.lineEdit.setObjectName(u"lineEdit")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineEdit.sizePolicy().hasHeightForWidth())
        self.lineEdit.setSizePolicy(sizePolicy)
        self.lineEdit.setMaxLength(50)

        self.verticalLayout_2.addWidget(self.lineEdit)

        self.lineEdit_2 = QLineEdit(self.verticalLayoutWidget)
        self.lineEdit_2.setObjectName(u"lineEdit_2")
        sizePolicy.setHeightForWidth(self.lineEdit_2.sizePolicy().hasHeightForWidth())
        self.lineEdit_2.setSizePolicy(sizePolicy)

        self.verticalLayout_2.addWidget(self.lineEdit_2)

        self.verticalLayout.addLayout(self.verticalLayout_2)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.authButton = QPushButton(self.verticalLayoutWidget)
        self.authButton.setObjectName(u"authButton")
        sizePolicy.setHeightForWidth(self.authButton.sizePolicy().hasHeightForWidth())
        self.authButton.setSizePolicy(sizePolicy)
        self.authButton.setMouseTracking(False)

        self.horizontalLayout.addWidget(self.authButton)

        self.registerButton = QPushButton(self.verticalLayoutWidget)
        self.registerButton.setObjectName(u"registerButton")
        sizePolicy.setHeightForWidth(self.registerButton.sizePolicy().hasHeightForWidth())
        self.registerButton.setSizePolicy(sizePolicy)

        self.horizontalLayout.addWidget(self.registerButton)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(AuthForm)

        QMetaObject.connectSlotsByName(AuthForm)

    # setupUi

    def retranslateUi(self, AuthForm):
        AuthForm.setWindowTitle(QCoreApplication.translate("AuthForm", u"Form", None))
        # if QT_CONFIG(tooltip)
        self.lineEdit.setToolTip("")
        # endif // QT_CONFIG(tooltip)
        self.lineEdit.setInputMask("")
        self.lineEdit.setText("")
        self.lineEdit.setPlaceholderText("")
        self.authButton.setText(QCoreApplication.translate("AuthForm",
                                                           u"\u0410\u0432\u0442\u043e\u0440\u0438\u0437\u0430\u0446\u0438\u044f",
                                                           None))
        self.registerButton.setText(QCoreApplication.translate("AuthForm",
                                                               u"\u0420\u0435\u0433\u0438\u0441\u0442\u0440\u0430\u0446\u0438\u044f",
                                                               None))
    # retranslateUi
