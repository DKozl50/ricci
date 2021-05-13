import sys
import enum

import networkx as nx
import numpy as np
from ricci_calculators import ollivier
from PyQt5.QtWidgets import QMainWindow, QApplication, \
    QPushButton, QVBoxLayout, QHBoxLayout, QWidget
from PyQt5.QtGui import QPalette, QPainter, QBrush, QPen, \
    QColor, QMouseEvent, QWheelEvent
from PyQt5.QtCore import QPointF, Qt


class MouseState(enum.Enum):
    released = 0
    down_idle = 1
    move_field = 2
    move_vertex = 3


class GraphView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBackgroundRole(QPalette.Base)
        self.setAutoFillBackground(True)

        self.scale_per_angle = .003
        self.scale = 1.
        self.max_scale = 5.
        self.min_scale = 0.5

        self.vertex_color = QColor(255, 69, 0)  # orangered
        self.vertex_border_color = QColor(0, 0, 0)  # black
        self.vertex_radius = 20
        self.edge_color = QColor(0, 0, 255)  # blue
        self.edge_size = 3

        self.mouse = MouseState.released
        self.mouse_pos = None
        self.moved_vertex = None

        self.offset = None
        self.v_offsets = None
        self.reset()

    def reset(self):
        self._get_graph()
        self.offset = np.array([0, 0], dtype=np.float32)
        self.v_offsets = np.zeros(self.coords.shape)

    def _get_graph(self):
        self.graph = [
            [1, 2],
            [3],
        ]
        self.coords = np.array([
            [-30, -60],
            [60, -30],
            [-90, 0],
            [30, 30],
        ], dtype=np.float32)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = painter.viewport().width(), painter.viewport().height()
        painter.setWindow(-w//2, -h//2, w, h)

        self._draw_edges(painter)
        self._draw_vertices(painter)

    def mousePressEvent(self, a0: QMouseEvent) -> None:
        if a0.button() == Qt.LeftButton:
            self.mouse_pos = np.array([
                a0.localPos().x() - self.width() / 2,
                a0.localPos().y() - self.height() / 2
            ])
            self.mouse = MouseState.down_idle
            for i, v in enumerate(self.coords):
                if self._inside_v(i, self.mouse_pos):
                    self.mouse = MouseState.move_vertex
                    self.moved_vertex = i

    def mouseMoveEvent(self, a0: QMouseEvent) -> None:
        pos = np.array([
            a0.localPos().x() - self.width() / 2,
            a0.localPos().y() - self.height() / 2
        ])

        if self.mouse == MouseState.move_vertex:
            self._move_vertex(pos)
        else:
            if self.mouse == MouseState.down_idle:
                self.mouse = MouseState.move_field
            self._move_field(pos)

        self.mouse_pos = pos
        self.repaint()

    def _move_vertex(self, pos: np.ndarray):
        self.v_offsets[self.moved_vertex] += (pos - self.mouse_pos) / self.scale

    def _move_field(self, pos: np.ndarray):
        self.offset += pos - self.mouse_pos

    def mouseReleaseEvent(self, a0: QMouseEvent) -> None:
        if a0.button() == Qt.LeftButton:
            self.mouse = MouseState.released

    def wheelEvent(self, a0: QWheelEvent) -> None:
        prev_scale = self.scale
        self.scale += self.scale_per_angle * a0.angleDelta().y()
        self.scale = min(self.max_scale, max(self.min_scale, self.scale))
        pos = np.array([a0.position().x() - self.width()/2, a0.position().y() - self.height()/2])
        self.offset += (1 - self.scale / prev_scale) * (pos - self.offset)
        self.repaint()

    def _draw_vertices(self, painter: QPainter):
        painter.setBrush(QBrush(self.vertex_color))
        painter.setPen(QPen(self.vertex_border_color, 0.5))
        for i in range(len(self.coords)):
            self._draw_vertex(painter, i)

    def _draw_edges(self, painter: QPainter):
        painter.setPen(QPen(self.edge_color, self.scale * self.edge_size))
        for i, v in enumerate(self.graph):
            for j in v:
                self._draw_edge(painter, i, j)

    def _v_center(self, i: int):
        return self.scale * (self.coords[i] + self.v_offsets[i]) + self.offset

    def _calc_coord(self, i: int):
        return QPointF(*self._v_center(i))

    def _inside_v(self, vertex_i: int, other: np.ndarray):
        vertex = self._v_center(vertex_i)
        dist2 = ((vertex - other)**2).sum()
        return dist2 < (self.vertex_radius * self.scale)**2

    def _draw_vertex(self, painter: QPainter, i: int):
        painter.drawEllipse(
            self._calc_coord(i),
            self.scale * self.vertex_radius,
            self.scale * self.vertex_radius
        )

    def _draw_edge(self, painter: QPainter, i: int, j: int):
        painter.drawLine(
            self._calc_coord(i),
            self._calc_coord(j)
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
