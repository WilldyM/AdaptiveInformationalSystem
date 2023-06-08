import operator

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *


class ScrollbarFilter(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress and obj.metaObject().className() == 'QScrollBar':
            scrollbar = obj
            pos = scrollbar.mapFromGlobal(QCursor.pos())
            opt = QStyleOptionSlider()
            scrollbar.initStyleOption(opt)
            groove_rect = scrollbar.style().subControlRect(QStyle.CC_ScrollBar, opt, QStyle.SC_ScrollBarGroove, scrollbar)
            slider_rect = scrollbar.style().subControlRect(QStyle.CC_ScrollBar, opt, QStyle.SC_ScrollBarSlider, scrollbar)
            if event.button() == Qt.LeftButton and not groove_rect.contains(pos) and pos.y() < slider_rect.top():
                min_val = scrollbar.minimum()
                max_val = scrollbar.maximum()
                single_step = scrollbar.singleStep()
                page_step = scrollbar.pageStep()
                value = scrollbar.value()
                if pos.y() >= slider_rect.top() - single_step:
                    scrollbar.setValue(max(value - single_step, min_val))
                else:
                    scrollbar.setValue(max(value - page_step, min_val))
                return True
        return super().eventFilter(obj, event)


class CustomTableView(QTableView):
    def __init__(self, data_list, header, *args, **kwargs):
        QTableView.__init__(self, *args, **kwargs)
        # self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setStyleSheet('''
        QHeaderView::section {
            background-color: #eee;
            color: #000;
            font: bold 12px;
            border: 1px solid #eee;
            padding: 5px;
            text-align: center;
        }
        QTableView::item {
            color: #555;
            font: 12px;
        }
        QTableView::item:selected {
            background: #eee;
        }
        ''')
        self.verticalScrollBar().installEventFilter(ScrollbarFilter(self.verticalScrollBar()))
        table_model = CustomTableModel(self, data_list, header)
        self.setModel(table_model)
        # set font
        # font = QFont("PT Mono", 10)
        # # self.setFont(font)
        # font_bold = QFont(font)
        # font_bold.setBold(True)
        # self.horizontalHeader().setFont(font_bold)
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
