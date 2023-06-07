import operator

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *


class CustomTableView(QTableView):
    def __init__(self, data_list, header, *args, **kwargs):
        QTableView.__init__(self, *args, **kwargs)
        table_model = CustomTableModel(self, data_list, header)
        self.setModel(table_model)
        # set font
        font = QFont("PT Mono", 10)
        self.setFont(font)
        font_bold = QFont(font)
        font_bold.setBold(True)
        self.horizontalHeader().setFont(font_bold)
        # set column width to fit contents (set font first!)
        self.resizeColumnsToContents()
        # enable sorting
        self.setSortingEnabled(True)


class CustomTableModel(QAbstractTableModel):
    def __init__(self, parent, mylist, header, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        self.mylist = mylist
        self.header = header

    def rowCount(self, parent):
        return len(self.mylist)

    def columnCount(self, parent):
        return len(self.mylist[0])

    def data(self, index, role):
        if not index.isValid():
            return None
        elif role != Qt.DisplayRole:
            return None
        return self.mylist[index.row()][index.column()]

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[col]
        return None

    def sort(self, col, order):
        """sort table by given column number col"""
        try:
            self.emit(SIGNAL("layoutAboutToBeChanged()"))
            self.mylist = sorted(self.mylist, key=operator.itemgetter(col))
            if order == Qt.DescendingOrder:
                self.mylist.reverse()
            self.emit(SIGNAL("layoutChanged()"))
        except TypeError:
            return
