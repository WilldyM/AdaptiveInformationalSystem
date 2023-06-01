# -*- coding: utf-8 -*-

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
                            QMetaObject, QObject, QPoint, QRect,
                            QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
                           QFont, QFontDatabase, QGradient, QIcon,
                           QImage, QKeySequence, QLinearGradient, QPainter,
                           QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QHeaderView, QSizePolicy,
                               QTreeWidget, QTreeWidgetItem, QWidget)


class Ui_ModelForm(object):
    def setupUi(self, ModelForm):
        if not ModelForm.objectName():
            ModelForm.setObjectName(u"ModelForm")
        ModelForm.resize(672, 500)
        self.horizontalLayoutWidget = QWidget(ModelForm)
        self.horizontalLayoutWidget.setObjectName(u"horizontalLayoutWidget")
        self.horizontalLayoutWidget.setGeometry(QRect(0, 0, 671, 501))
        self.horizontalLayout = QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.modelTreeManagement = QTreeWidget(self.horizontalLayoutWidget)
        self.modelTreeManagement.setObjectName(u"modelTreeManagement")
        self.modelTreeManagement.setEnabled(True)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.modelTreeManagement.sizePolicy().hasHeightForWidth())
        self.modelTreeManagement.setSizePolicy(sizePolicy)
        self.modelTreeManagement.setBaseSize(QSize(0, 0))
        self.modelTreeManagement.header().setVisible(True)

        self.horizontalLayout.addWidget(self.modelTreeManagement)

        self.tupleTreeManagement = QTreeWidget(self.horizontalLayoutWidget)
        self.tupleTreeManagement.setObjectName(u"tupleTreeManagement")

        self.horizontalLayout.addWidget(self.tupleTreeManagement)

        self.retranslateUi(ModelForm)

        QMetaObject.connectSlotsByName(ModelForm)

    # setupUi

    def retranslateUi(self, ModelForm):
        ModelForm.setWindowTitle(QCoreApplication.translate("ModelForm", u"Form", None))
        ___qtreewidgetitem = self.modelTreeManagement.headerItem()
        ___qtreewidgetitem.setText(0, QCoreApplication.translate("ModelForm",
                                                                 u"\u0423\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u0435 \u043c\u043e\u0434\u0435\u043b\u044c\u044e",
                                                                 None));
        ___qtreewidgetitem1 = self.tupleTreeManagement.headerItem()
        ___qtreewidgetitem1.setText(0, QCoreApplication.translate("ModelForm",
                                                                  u"\u041a\u043e\u0440\u0442\u0435\u0436\u0438 \u0432\u044b\u0440\u0430\u0436\u0435\u043d\u0438\u044f",
                                                                  None));
    # retranslateUi
