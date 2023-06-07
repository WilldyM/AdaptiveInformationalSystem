# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'tt_tuple_part_set_c_object.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QHBoxLayout, QLayout,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget)

class Ui_TtTuplePartSetCObject(object):
    def setupUi(self, TtTuplePartSetCObject):
        if not TtTuplePartSetCObject.objectName():
            TtTuplePartSetCObject.setObjectName(u"TtTuplePartSetCObject")
        TtTuplePartSetCObject.resize(271, 151)
        self.verticalLayoutWidget = QWidget(TtTuplePartSetCObject)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayoutWidget.setGeometry(QRect(60, 30, 160, 99))
        self.verticalLayout_2 = QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.comboBox = QComboBox(self.verticalLayoutWidget)
        self.comboBox.setObjectName(u"comboBox")

        self.verticalLayout_2.addWidget(self.comboBox)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.pushButton_3 = QPushButton(self.verticalLayoutWidget)
        self.pushButton_3.setObjectName(u"pushButton_3")
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_3.sizePolicy().hasHeightForWidth())
        self.pushButton_3.setSizePolicy(sizePolicy)

        self.horizontalLayout_2.addWidget(self.pushButton_3)

        self.pushButton_4 = QPushButton(self.verticalLayoutWidget)
        self.pushButton_4.setObjectName(u"pushButton_4")
        sizePolicy.setHeightForWidth(self.pushButton_4.sizePolicy().hasHeightForWidth())
        self.pushButton_4.setSizePolicy(sizePolicy)

        self.horizontalLayout_2.addWidget(self.pushButton_4)


        self.verticalLayout_2.addLayout(self.horizontalLayout_2)


        self.retranslateUi(TtTuplePartSetCObject)
        self.pushButton_4.clicked.connect(TtTuplePartSetCObject.close)

        QMetaObject.connectSlotsByName(TtTuplePartSetCObject)
    # setupUi

    def retranslateUi(self, TtTuplePartSetCObject):
        TtTuplePartSetCObject.setWindowTitle(QCoreApplication.translate("TtTuplePartSetCObject", u"\u0423\u0441\u0442\u0430\u043d\u043e\u0432\u043a\u0430 \u043e\u0431\u044a\u0435\u043a\u0442\u0430", None))
        self.comboBox.setCurrentText("")
        self.comboBox.setPlaceholderText(QCoreApplication.translate("TtTuplePartSetCObject", u"\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u043e\u0431\u044a\u0435\u043a\u0442...", None))
        self.pushButton_3.setText(QCoreApplication.translate("TtTuplePartSetCObject", u"\u041e\u043a", None))
#if QT_CONFIG(shortcut)
        self.pushButton_3.setShortcut(QCoreApplication.translate("TtTuplePartSetCObject", u"Return", None))
#endif // QT_CONFIG(shortcut)
        self.pushButton_4.setText(QCoreApplication.translate("TtTuplePartSetCObject", u"\u041e\u0442\u043c\u0435\u043d\u0430", None))
#if QT_CONFIG(shortcut)
        self.pushButton_4.setShortcut(QCoreApplication.translate("TtTuplePartSetCObject", u"Esc", None))
#endif // QT_CONFIG(shortcut)
    # retranslateUi

