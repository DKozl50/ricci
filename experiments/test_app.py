import sys
import enum
from typing import Union

import networkx as nx
import numpy as np
from ricci_calculators import ollivier, forman
from PyQt5.QtWidgets import QMainWindow, QApplication, \
    QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QLabel, \
    QRadioButton, QGroupBox
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
        self.vertex_radius = 4
        self.default_edge_color = QColor(0, 0, 0)  # blue
        self.max_edge_color = QColor(200, 0, 0)
        self.min_edge_color = QColor(0, 0, 255)
        self.edge_size = 1
        self.graph_convert_scale = 2 * self.width()

        self.mouse = MouseState.released
        self.mouse_pos = None
        self.moved_vertex = None

        self.offset = None
        self.v_offsets = None

        self.graph = None
        self.params = None
        self.curr_param = -1
        self.vertex_count = 0
        self.coords = None

        self._init_graph()
        self.reset()

    def reset(self):
        self.offset = np.array([0, 0], dtype=np.float32)
        self.scale = 1
        self.v_offsets = np.zeros(self.coords.shape)
        self.repaint()

    def _init_graph(self):
        # probably will not be used, but for a good measure
        self.set_graph(np.array([
            [0, 1, 0, 0],
            [1, 0, 1, 0],
            [0, 1, 0, 1],
            [0, 0, 1, 0],
        ]))

    def set_graph(self, mat: np.ndarray):
        self.graph = mat
        self.vertex_count = self.graph.shape[0]
        pos = nx.spring_layout(nx.from_numpy_matrix(self.graph))
        self.coords = np.array(list(pos.values()), dtype=np.float32) * self.graph_convert_scale
        self.reset()
        self.repaint()

    def set_params(self, **kwargs):
        self.params = kwargs

    def change_param(self, key: Union[int, str]):
        self.curr_param = key
        self.repaint()

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
        if self.curr_param == -1:
            mode = 1
        else:
            mode = -1
        # if self.param is None:
        #     color_mode = 1
        # else:
        #     color_mode = -1
        for i in range(self.vertex_count):
            for j in range(i+1, self.vertex_count):
                # TODO check if it is oriented

                # check if edge is present
                if self.graph[i, j] != 0:
                    self._draw_edge(painter, i, j, mode)

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

    def _draw_edge(self, painter: QPainter, i: int, j: int, mode: int):
        if mode == 1:
            painter.setPen(QPen(self.default_edge_color, self.scale * self.edge_size))
        elif mode == -1:
            c_val = self.params[self.curr_param]
            emin = c_val.min()
            delta = c_val.max() - emin
            cur_coef = (c_val[i, j]-emin) / delta
            curr_col = QColor(
                int(
                    cur_coef * self.max_edge_color.red() +
                    (1 - cur_coef) * self.min_edge_color.red()
                ),
                int(
                    cur_coef * self.max_edge_color.green() +
                    (1 - cur_coef) * self.min_edge_color.green()
                ),
                int(
                    cur_coef * self.max_edge_color.blue() +
                    (1 - cur_coef) * self.min_edge_color.blue()
                )
            )
            painter.setPen(QPen(curr_col, self.scale * self.edge_size))

        painter.drawLine(
            self._calc_coord(i),
            self._calc_coord(j)
        )


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.resize(750, 600)

        self.view = GraphView(self)
        self.click_info = QLabel(self)
        self.view_type_box = QGroupBox(self)
        self.vt_default_rb = QRadioButton(self)
        self.vt_ollivier_rb = QRadioButton(self)
        self.vt_forman_rb = QRadioButton(self)
        self.refresh_button = QPushButton(self)
        self.new_graph_button = QPushButton(self)

        self.graph = None

        self._init_ui()
        self._init_elements()

    def _init_ui(self):
        view_type_box_layout = QVBoxLayout(self)
        view_type_box_layout.addWidget(self.vt_default_rb)
        view_type_box_layout.addWidget(self.vt_ollivier_rb)
        view_type_box_layout.addWidget(self.vt_forman_rb)
        self.view_type_box.setLayout(view_type_box_layout)

        right_layout = QVBoxLayout(self)
        right_layout.addWidget(self.click_info)
        right_layout.addWidget(self.view_type_box)
        right_layout.addWidget(self.refresh_button)
        right_layout.addWidget(self.new_graph_button)

        main_layout = QHBoxLayout(self)
        main_layout.addWidget(self.view)
        main_layout.addLayout(right_layout)

        widget = QWidget()
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)

    def _init_elements(self):
        self._init_graph()
        self._init_info()
        self._init_view_type()
        self._init_buttons()
        self.show()

    def _init_graph(self):
        self.new_graph()

    def _init_info(self):
        self.click_info.setText('Click on an edge to get information')

    def _init_view_type(self):
        self.view_type_box.setTitle('Choose edge information')
        self.vt_default_rb.setText('Nothing')
        self.vt_default_rb.toggled.connect(self.set_default_view)
        self.vt_ollivier_rb.setText('Ollivier')
        self.vt_ollivier_rb.toggled.connect(self.set_ollivier_view)
        self.vt_forman_rb.setText('Forman')
        self.vt_forman_rb.toggled.connect(self.set_forman_view)

        self.vt_default_rb.setChecked(True)

    def _init_buttons(self):
        self.refresh_button.setText('Reset view')
        self.refresh_button.clicked.connect(self.reset_handler)
        self.new_graph_button.setText('New graph')
        self.new_graph_button.clicked.connect(self.new_graph)

    def set_default_view(self):
        if self.sender().isChecked():
            self.view.change_param(-1)

    def set_ollivier_view(self):
        if self.sender().isChecked():
            self.view.change_param('ollivier')

    def set_forman_view(self):
        if self.sender().isChecked():
            self.view.change_param('forman')

    def reset_handler(self):
        self.view.curr_param = -1
        self.view.reset()

    def new_graph(self):
        self.graph = nx.random_geometric_graph(50, 0.125)
        ollivier(self.graph)
        forman(self.graph)
        self.view.set_graph(nx.adjacency_matrix(self.graph).toarray())
        self.view.set_params(
            ollivier=nx.adjacency_matrix(self.graph, weight='ollivier').toarray(),
            forman=nx.adjacency_matrix(self.graph, weight='forman').toarray(),
        )


print('step 1')
app = QApplication(sys.argv)
print('step 2')
window = MainWindow()
print('step 3')
app.exec_()
