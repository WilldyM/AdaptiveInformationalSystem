# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'tt_tuple_part_rename.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLayout, QLineEdit,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget)

class Ui_TtTuplePartRename(object):
    def setupUi(self, TtTuplePartRename):
        if not TtTuplePartRename.objectName():
            TtTuplePartRename.setObjectName(u"TtTuplePartRename")
        TtTuplePartRename.resize(274, 137)
        self.verticalLayoutWidget = QWidget(TtTuplePartRename)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayoutWidget.setGeometry(QRect(60, 30, 160, 99))
        self.verticalLayout = QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.lineEdit = QLineEdit(self.verticalLayoutWidget)
        self.lineEdit.setObjectName(u"lineEdit")

        self.verticalLayout.addWidget(self.lineEdit)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.pushButton = QPushButton(self.verticalLayoutWidget)
        self.pushButton.setObjectName(u"pushButton")
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton.sizePolicy().hasHeightForWidth())
        self.pushButton.setSizePolicy(sizePolicy)

        self.horizontalLayout.addWidget(self.pushButton)

        self.pushButton_2 = QPushButton(self.verticalLayoutWidget)
        self.pushButton_2.setObjectName(u"pushButton_2")
        sizePolicy.setHeightForWidth(self.pushButton_2.sizePolicy().hasHeightForWidth())
        self.pushButton_2.setSizePolicy(sizePolicy)

        self.horizontalLayout.addWidget(self.pushButton_2)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(TtTuplePartRename)
        self.pushButton_2.clicked.connect(TtTuplePartRename.close)

        QMetaObject.connectSlotsByName(TtTuplePartRename)
    # setupUi

    def retranslateUi(self, TtTuplePartRename):
        TtTuplePartRename.setWindowTitle(QCoreApplication.translate("TtTuplePartRename", u"\u041f\u0435\u0440\u0435\u0438\u043c\u0435\u043d\u043e\u0432\u0430\u043d\u0438\u0435 \u043e\u043f\u0435\u0440\u0430\u043d\u0434\u0430", None))
        self.pushButton.setText(QCoreApplication.translate("TtTuplePartRename", u"\u041e\u043a", None))
#if QT_CONFIG(shortcut)
        self.pushButton.setShortcut(QCoreApplication.translate("TtTuplePartRename", u"Return", None))
#endif // QT_CONFIG(shortcut)
        self.pushButton_2.setText(QCoreApplication.translate("TtTuplePartRename", u"\u041e\u0442\u043c\u0435\u043d\u0430", None))
#if QT_CONFIG(shortcut)
        self.pushButton_2.setShortcut(QCoreApplication.translate("TtTuplePartRename", u"Esc", None))
#endif // QT_CONFIG(shortcut)
    # retranslateUi

