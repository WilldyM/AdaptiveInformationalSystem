# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'on_expression_add_field.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QHBoxLayout,
    QLayout, QPushButton, QSizePolicy, QVBoxLayout,
    QWidget)

import config



class Ui_OnExpressionAddField(object):
    def setupUi(self, OnExpressionAddField):
        if not OnExpressionAddField.objectName():
            OnExpressionAddField.setObjectName(u"OnExpressionAddField")
        OnExpressionAddField.resize(281, 161)
        self.verticalFrame = QFrame(OnExpressionAddField)
        self.verticalFrame.setObjectName(u"verticalFrame")
        self.verticalFrame.setGeometry(QRect(0, 0, 281, 161))
        url_arrow = config.ARROW_PNG.replace("\\", "/")
        self.verticalFrame.setStyleSheet(u"QFrame {\n"
"\n"
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
"QComboBox {\n"
"margin-top: 30px;\n"
"margin-left: 50%;\n"
"margin-right: 50%;\n"
"max-height: 30px;\n"
"min-height: 30px;\n"
"background-color: #F4F4F4;\n"
"color: #404040;\n"
"border: 1px solid #ccc;\n"
"padding: 2px 18px 2px 10px;\n"
"border-radius: 4px;\n"
"}\n"
"\n"
"QComboBox:hover, ComboBox:focus {\n"
"    background-color: #FFFFFF;\n"
"    border: 1px solid #9B9B9B;\n"
"}\n"
"\n"
"QComboBox::drop-down {\n"
"    subcontrol-origin: margin;\n"
"    subcontrol-position: center right;\n"
"    width: 15px;\n"
"	margin-top: 30px;\n"
"	border: n"
                        "one;\n"
"	border-radius: 2px;\n"
"}\n"
"\n"
"QComboBox::down-arrow {\n"
f"image: url(\"{url_arrow}\");\n"
"    width: 12px;\n"
"    height: 12px;\n"
"margin-right: 100%;\n"
"}\n"
"\n"
"QComboBox::item {\n"
"margin: 0px;\n"
"padding: 2px;\n"
"text-align: left;\n"
"background-color: transparent;\n"
"}\n"
"\n"
"\n"
"")
        self.verticalLayout_2 = QVBoxLayout(self.verticalFrame)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.comboBox = QComboBox(self.verticalFrame)
        self.comboBox.setObjectName(u"comboBox")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.comboBox.sizePolicy().hasHeightForWidth())
        self.comboBox.setSizePolicy(sizePolicy)
        self.comboBox.setStyleSheet(u"")
        self.comboBox.setSizeAdjustPolicy(QComboBox.AdjustToContentsOnFirstShow)

        self.verticalLayout_2.addWidget(self.comboBox)

        self.horizontalFrame = QFrame(self.verticalFrame)
        self.horizontalFrame.setObjectName(u"horizontalFrame")
        self.horizontalLayout_2 = QHBoxLayout(self.horizontalFrame)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.pushButton_3 = QPushButton(self.horizontalFrame)
        self.pushButton_3.setObjectName(u"pushButton_3")
        sizePolicy.setHeightForWidth(self.pushButton_3.sizePolicy().hasHeightForWidth())
        self.pushButton_3.setSizePolicy(sizePolicy)
        self.pushButton_3.setStyleSheet(u"margin-left: 40%;")

        self.horizontalLayout_2.addWidget(self.pushButton_3)

        self.pushButton_4 = QPushButton(self.horizontalFrame)
        self.pushButton_4.setObjectName(u"pushButton_4")
        sizePolicy.setHeightForWidth(self.pushButton_4.sizePolicy().hasHeightForWidth())
        self.pushButton_4.setSizePolicy(sizePolicy)
        self.pushButton_4.setStyleSheet(u"margin-right: 40%;")

        self.horizontalLayout_2.addWidget(self.pushButton_4)


        self.verticalLayout_2.addWidget(self.horizontalFrame)


        self.retranslateUi(OnExpressionAddField)
        self.pushButton_4.clicked.connect(OnExpressionAddField.close)

        QMetaObject.connectSlotsByName(OnExpressionAddField)
    # setupUi

    def retranslateUi(self, OnExpressionAddField):
        OnExpressionAddField.setWindowTitle(QCoreApplication.translate("OnExpressionAddField", u"\u0414\u043e\u0431\u0430\u0432\u043b\u0435\u043d\u0438\u0435 \u0441\u0442\u043e\u043b\u0431\u0446\u0430", None))
        self.comboBox.setCurrentText("")
        self.comboBox.setPlaceholderText(QCoreApplication.translate("OnExpressionAddField", u"\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u043e\u0431\u044a\u0435\u043a\u0442...", None))
        self.pushButton_3.setText(QCoreApplication.translate("OnExpressionAddField", u"\u041e\u043a", None))
#if QT_CONFIG(shortcut)
        self.pushButton_3.setShortcut(QCoreApplication.translate("OnExpressionAddField", u"Return", None))
#endif // QT_CONFIG(shortcut)
        self.pushButton_4.setText(QCoreApplication.translate("OnExpressionAddField", u"\u041e\u0442\u043c\u0435\u043d\u0430", None))
#if QT_CONFIG(shortcut)
        self.pushButton_4.setShortcut(QCoreApplication.translate("OnExpressionAddField", u"Esc", None))
#endif // QT_CONFIG(shortcut)
    # retranslateUi

