# -*- coding: utf-8 -*-

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
                            QMetaObject, QObject, QPoint, QRect,
                            QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
                           QFont, QFontDatabase, QGradient, QIcon,
                           QImage, QKeySequence, QLinearGradient, QPainter,
                           QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLayout, QLineEdit,
                               QPushButton, QSizePolicy, QVBoxLayout, QWidget)


class Ui_MtModelCreate(object):
    def setupUi(self, MtModelCreate):
        if not MtModelCreate.objectName():
            MtModelCreate.setObjectName(u"MtModelCreate")
        MtModelCreate.resize(273, 138)
        self.verticalLayoutWidget = QWidget(MtModelCreate)
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

        self.retranslateUi(MtModelCreate)
        self.pushButton_2.clicked.connect(MtModelCreate.close)

        QMetaObject.connectSlotsByName(MtModelCreate)

    # setupUi

    def retranslateUi(self, MtModelCreate):
        MtModelCreate.setWindowTitle(QCoreApplication.translate("MtModelCreate", u"Form", None))
        self.pushButton.setText(
            QCoreApplication.translate("MtModelCreate", u"\u0421\u043e\u0437\u0434\u0430\u0442\u044c", None))
        # if QT_CONFIG(shortcut)
        self.pushButton.setShortcut(QCoreApplication.translate("MtModelCreate", u"Return", None))
        # endif // QT_CONFIG(shortcut)
        self.pushButton_2.setText(
            QCoreApplication.translate("MtModelCreate", u"\u041e\u0442\u043c\u0435\u043d\u0430", None))
        # if QT_CONFIG(shortcut)
        self.pushButton_2.setShortcut(QCoreApplication.translate("MtModelCreate", u"Esc", None))
# endif // QT_CONFIG(shortcut)
# retranslateUi
