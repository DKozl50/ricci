import sys
import networkx as nx
from ricci_calculators import ollivier
from PyQt5.QtWidgets import QMainWindow, QApplication, \
                            QPushButton, QVBoxLayout, QHBoxLayout, QWidget
from PyQt5.QtGui import QPalette, QPainter, QBrush, QColor
# delete me
from random import randint


class GraphView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBackgroundRole(QPalette.Base)
        self.setAutoFillBackground(True)

    def paintEvent(self, event):
        print('drawing!')
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # painter.setBrush(QBrush(QColor(randint(0, 255), randint(0, 255), randint(0, 255))))

        w, h = painter.device().width(), painter.device().height()

        grid_side = 10
        for i in range(grid_side):
            for j in range(grid_side):
                painter.setBrush(QBrush(QColor(randint(0, 255), randint(0, 255), randint(0, 255))))
                painter.drawEllipse(i*w//10, j*h//10, w//10, h//10)
        # fast indeed


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.resize(750, 600)

        self.view = GraphView(self)
        self.ollivier_button = QPushButton(self)
        self.forman_button = QPushButton(self)
        self.refresh_button = QPushButton(self)

        self._init_ui()
        self._init_elements()

    def _init_ui(self):

        right_layout = QVBoxLayout(self)
        right_layout.addWidget(self.ollivier_button)
        right_layout.addWidget(self.forman_button)
        right_layout.addWidget(self.refresh_button)

        main_layout = QHBoxLayout(self)
        main_layout.addWidget(self.view)
        main_layout.addLayout(right_layout)

        widget = QWidget()
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)

    def _init_elements(self):
        self._init_graph()
        # self._init_gview()
        self._init_buttons()
        self.show()

    def _init_graph(self):
        self.graph = nx.random_geometric_graph(50, 0.125)
        # _fix_graph(self.graph)
        ollivier(self.graph)

    def _init_buttons(self):
        self.ollivier_button.setText('Ollivier')
        self.ollivier_button.clicked.connect(self.ollivier_handler)
        self.forman_button.setText('Forman')
        self.forman_button.clicked.connect(self.forman_handler)
        self.refresh_button.setText('Refresh network')
        # self.refresh_button.clicked.connect(self.update_gview)

    def ollivier_handler(self):
        pass

    def forman_handler(self):
        pass


print('step 1')
app = QApplication(sys.argv)
print('step 2')
window = MainWindow()
print('step 3')
app.exec_()
