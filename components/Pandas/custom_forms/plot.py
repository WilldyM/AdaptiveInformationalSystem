import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
import pyqtgraph as pg
import numpy as np


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide6 with PyQtGraph")
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()
        widget = pg.PlotWidget()
        layout.addWidget(widget)

        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        widget.plot(x, y)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
