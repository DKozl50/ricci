import sys
import networkx as nx
import numpy as np
from ricci_calculators import ollivier
from PyQt5.QtWidgets import QMainWindow, QApplication, \
    QPushButton, QVBoxLayout, QHBoxLayout, QWidget
from PyQt5.QtGui import QPalette, QPainter, QBrush, QPen, \
    QColor, QWheelEvent
from PyQt5.QtCore import QPointF


class GraphView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBackgroundRole(QPalette.Base)
        self.setAutoFillBackground(True)

        self.scale_per_angle = .005
        self.scale = 1.
        self.max_scale = 5.
        self.min_scale = 0.2

        self.vertex_color = QColor(255, 69, 0)  # orangered
        self.vertex_radius = 20
        self.edge_color = QColor(0, 0, 255)  # black
        self.edge_size = 3

        self.graph = [
            [1, 2],
            [3],
        ]
        self.coords = self.coords_real = np.array([
            [-30, -60],
            [60, -30],
            [-90, 0],
            [30, 30],
        ], dtype=np.float32)
        self.offset = np.array([0, 0], dtype=np.float32)

    def _get_graph(self):
        self.graph = [
            [1, 2],
            [3],
        ]
        self.coords_real = np.array([
            [-30, -60],
            [60, -30],
            [-90, 0],
            [30, 30],
        ], dtype=np.float32)
        self.coords = self.coords_real
        self.offset = np.array([0, 0], dtype=np.float32)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = painter.viewport().width(), painter.viewport().height()
        painter.setWindow(-w//2, -h//2, w, h)

        self._draw_edges(painter)
        self._draw_vertices(painter)

    def wheelEvent(self, a0: QWheelEvent) -> None:
        prev_scale = self.scale
        self.scale += self.scale_per_angle * a0.angleDelta().y()
        self.scale = min(self.max_scale, max(self.min_scale, self.scale))
        pos = np.array([a0.position().x() - self.width()/2, a0.position().y() - self.height()/2])
        self.offset += (1 - self.scale / prev_scale) * (pos - self.offset)
        self.coords = self.scale * self.coords_real
        self.repaint()

    def _draw_vertices(self, painter: QPainter):
        painter.setBrush(QBrush(self.vertex_color))
        painter.setPen(QPen(painter.brush(), 1))
        for i in range(len(self.coords)):
            self._draw_vertex(painter, i)

    def _draw_edges(self, painter: QPainter):
        painter.setPen(QPen(self.edge_color, self.scale * self.edge_size))
        for i, v in enumerate(self.graph):
            for j in v:
                self._draw_edge(painter, i, j)

    def _draw_vertex(self, painter: QPainter, i: int):
        painter.drawEllipse(
            QPointF(*(self.scale * self.coords_real[i] + self.offset)),
            self.scale * self.vertex_radius,
            self.scale * self.vertex_radius
        )

    def _draw_edge(self, painter: QPainter, i: int, j: int):
        painter.drawLine(
            QPointF(*(self.scale * self.coords_real[i] + self.offset)),
            QPointF(*(self.scale * self.coords_real[j] + self.offset))
        )


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
