# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'on_create_table.ui'
##
## Created by: Qt User Interface Compiler version 6.5.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLayout,
    QLineEdit, QPushButton, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_OnCreateTable(object):
    def setupUi(self, OnCreateTable):
        if not OnCreateTable.objectName():
            OnCreateTable.setObjectName(u"OnCreateTable")
        OnCreateTable.resize(271, 131)
        self.verticalFrame = QFrame(OnCreateTable)
        self.verticalFrame.setObjectName(u"verticalFrame")
        self.verticalFrame.setGeometry(QRect(0, 0, 271, 131))
        self.verticalFrame.setStyleSheet(u"QFrame {\n"
"margin: 0 50%;\n"
"}\n"
"QPushButton {\n"
"margin-top: 10px; \n"
"margin-bottom: 20px;\n"
"margin-left: 0px;\n"
"margin-right: 0px;\n"
"max-height: 30px;\n"
"min-height: 30px;\n"
"background-color: rgba(255, 255, 255, 20%); \n"
"border: 1px solid #ccc;\n"
"border-radius: 4px;\n"
"padding: 0;\n"
"}\n"
"QPushButton:hover {\n"
"    background-color: rgba(255, 255, 255, 80%);\n"
"}\n"
"QPushButton:pressed {\n"
"    background-color: rgba(255, 255, 255, 100%);\n"
"}\n"
"\n"
"QLineEdit {\n"
"margin-top: 30px;\n"
"max-height: 30px;\n"
"min-height: 30px;\n"
"background-color: #F4F4F4;\n"
"color: #404040;\n"
"border: 1px solid #ccc;\n"
"padding: 1px 5px;\n"
"border-radius: 4px;\n"
"}\n"
"\n"
"QLineEdit:hover, QLineEdit:focus {\n"
"    background-color: #FFFFFF;\n"
"    border: 1px solid #9B9B9B;\n"
"}\n"
"")
        self.verticalLayout = QVBoxLayout(self.verticalFrame)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.lineEdit = QLineEdit(self.verticalFrame)
        self.lineEdit.setObjectName(u"lineEdit")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineEdit.sizePolicy().hasHeightForWidth())
        self.lineEdit.setSizePolicy(sizePolicy)

        self.verticalLayout.addWidget(self.lineEdit)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.pushButton = QPushButton(self.verticalFrame)
        self.pushButton.setObjectName(u"pushButton")
        sizePolicy.setHeightForWidth(self.pushButton.sizePolicy().hasHeightForWidth())
        self.pushButton.setSizePolicy(sizePolicy)

        self.horizontalLayout.addWidget(self.pushButton)

        self.pushButton_2 = QPushButton(self.verticalFrame)
        self.pushButton_2.setObjectName(u"pushButton_2")
        sizePolicy.setHeightForWidth(self.pushButton_2.sizePolicy().hasHeightForWidth())
        self.pushButton_2.setSizePolicy(sizePolicy)

        self.horizontalLayout.addWidget(self.pushButton_2)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(OnCreateTable)
        self.pushButton_2.clicked.connect(OnCreateTable.close)

        QMetaObject.connectSlotsByName(OnCreateTable)
    # setupUi

    def retranslateUi(self, OnCreateTable):
        OnCreateTable.setWindowTitle(QCoreApplication.translate("OnCreateTable", u"\u0421\u043e\u0437\u0434\u0430\u043d\u0438\u0435 \u0442\u0430\u0431\u043b\u0438\u0446\u044b", None))
        self.pushButton.setText(QCoreApplication.translate("OnCreateTable", u"\u041e\u043a", None))
#if QT_CONFIG(shortcut)
        self.pushButton.setShortcut(QCoreApplication.translate("OnCreateTable", u"Return", None))
#endif // QT_CONFIG(shortcut)
        self.pushButton_2.setText(QCoreApplication.translate("OnCreateTable", u"\u041e\u0442\u043c\u0435\u043d\u0430", None))
#if QT_CONFIG(shortcut)
        self.pushButton_2.setShortcut(QCoreApplication.translate("OnCreateTable", u"Esc", None))
#endif // QT_CONFIG(shortcut)
    # retranslateUi

