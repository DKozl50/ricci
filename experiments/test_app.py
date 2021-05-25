import sys
import enum
from typing import Union

import networkx as nx
import numpy as np
import ricci_calculator as rc
from PyQt5.QtWidgets import QMainWindow, QApplication, \
    QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QLabel, \
    QRadioButton, QGroupBox, QFileDialog
from PyQt5.QtGui import QPalette, QPainter, QBrush, QPen, \
    QColor, QMouseEvent, QWheelEvent, QPainterPath
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

        self.info_field: Union[QLabel, None] = None
        self.info_field_default_text = ''

        self.scale_per_angle = .003
        self.scale = 1.
        self.max_scale = 5.
        self.min_scale = 0.5

        self.vertex_radius = 4
        self.edge_size = 1
        self.graph_convert_scale = 2 * self.width()
        self.orient_edge_control_offset = 2.5
        self.triangle_size = 4
        self.highlight_mul = 1.7

        self.edge_detection_threshold_absolute = 300

        self.vertex_color = QColor(200, 200, 200)  # gray
        self.vertex_border_color = QColor(0, 0, 0)  # black
        self.default_edge_color = QColor(0, 0, 0)  # black
        self.max_edge_color = QColor(255, 0, 0)  # red
        self.min_edge_color = QColor(0, 0, 255)  # blue
        self.highlight_color = QColor(0, 255, 0)  # yellow

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
        self.symmertic = True
        self.highlighted_edge = None

        self._init_graph()
        self.reset(True)

    def connect_info_field(self, a0):
        self.info_field = a0
        self.info_field_default_text = a0.text()

    def update_info(self):
        if self.highlighted_edge is None:
            self.info_field.setText(self.info_field_default_text)
            return
        (i, j) = self.highlighted_edge
        self.info_field.setText(
            'Edge weight:  \t%.5g\n' % self.graph[i, j]
            + 'Ollivier curvature:  \t%.5g\n' % self.params['ollivier'][i, j]
            + 'Forman curvature:  \t%.5g\n' % self.params['forman'][i, j]
        )

    def reset(self, hard=False):
        self.offset = np.array([0, 0], dtype=np.float32)
        self.scale = 1
        if hard:
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
        self.symmertic = (mat.T == mat).all().all()
        self.vertex_count = self.graph.shape[0]
        pos = nx.spring_layout(
            nx.from_numpy_array(self.graph),
            k=np.sqrt(np.sqrt(rc.connected_components(self.graph))/self.vertex_count)
        )
        self.coords = np.array(list(pos.values()), dtype=np.float32) * self.graph_convert_scale
        self.reset(True)
        self.repaint()

    def set_params(self, **kwargs):
        self.params = kwargs
        self.repaint()

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
            for i in range(self.vertex_count):
                if self._inside_v(i, self.mouse_pos):
                    self.mouse = MouseState.move_vertex
                    self.moved_vertex = i
                    return

            closest_len2 = float('inf')
            closest_edge = (1, 1)
            for i in range(self.vertex_count):
                for j in range(self.vertex_count):
                    if i == j:
                        continue
                    if self.graph[i, j] != 0:
                        if (curr_dist := self._distance_to_e2(i, j, self.mouse_pos)) < closest_len2:
                            closest_len2 = curr_dist
                            closest_edge = (i, j)
            if closest_len2 <= self.edge_detection_threshold_absolute:
                self.highlighted_edge = closest_edge
            else:
                self.highlighted_edge = None
            self.update_info()
            self.repaint()

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

    def _v_center(self, i: int) -> np.ndarray:
        return self.scale * (self.coords[i] + self.v_offsets[i]) + self.offset

    def _calc_coord(self, i: int) -> QPointF:
        return QPointF(*self._v_center(i))

    def _inside_v(self, vertex_i: int, other: np.ndarray) -> bool:
        vertex = self._v_center(vertex_i)
        dist2 = ((vertex - other)**2).sum()
        return dist2 < (self.vertex_radius * self.scale)**2

    @staticmethod
    def _dist_to_segment2(a: np.ndarray, b: np.ndarray, p: np.ndarray) -> float:
        def d2(x, y):
            return ((x - y)**2).sum()
        e_len2 = d2(a, b)
        if e_len2 == 0:
            return d2(a, p)
        t = min(1, max(0, np.dot(p - a, b - a) / e_len2))
        proj = a + t * (b - a)
        return d2(proj, p)

    def _distance_to_e2(self, i: int, j: int, other: np.ndarray) -> float:
        if self.symmertic:
            return self._dist_to_segment2(self._v_center(i), self._v_center(j), other)
        else:
            # TODO offset by 1/2 self.orient_edge_control_offset
            pass

    def _draw_vertex(self, painter: QPainter, i: int):
        painter.drawEllipse(
            self._calc_coord(i),
            self.scale * self.vertex_radius,
            self.scale * self.vertex_radius
        )

    def _draw_edges(self, painter: QPainter):
        if self.curr_param == -1:
            mode = 1
            norm_param = self.graph
        else:
            mode = -1
            norm_param = self.params[self.curr_param]
            n_min = norm_param[self.graph != 0].min()
            n_delta = norm_param[self.graph != 0].max() - n_min
            if n_delta == 0:
                norm_param = np.ones(norm_param.shape) / 2  # set 0.5 everywhere
            else:
                norm_param = (norm_param - n_min) / n_delta

        if self.highlighted_edge is not None:
            self._highlight_edge(painter)

        for i in range(self.vertex_count):
            for j in range(i+1, self.vertex_count):
                if self.symmertic:
                    self._draw_edge_sym(painter, i, j, mode, norm_param[i, j])
                else:
                    self._draw_edge_ori(painter, i, j, mode, norm_param[i, j])
                    self._draw_edge_ori(painter, j, i, mode, norm_param[j, i])

    def _highlight_edge(self, painter: QPainter):
        if self.symmertic:
            self._draw_edge_sym(painter, *self.highlighted_edge, -2, 0)
        else:
            self._draw_edge_ori(painter, *self.highlighted_edge, -2, 0)

    def _draw_edge_sym(self, painter: QPainter, i: int, j: int, mode: int, coef: float):
        if self.graph[i, j] == 0:
            return
        self._set_pen(painter, mode, coef)
        painter.drawLine(
            self._calc_coord(i),
            self._calc_coord(j)
        )

    def _draw_edge_ori(self, painter: QPainter, i: int, j: int, mode: int, coef: float):
        if self.graph[i, j] == 0:
            return
        self._set_pen(painter, mode, coef)
        path = QPainterPath()
        path.moveTo(self._calc_coord(i))
        a = self._v_center(i)
        b = self._v_center(j)
        ban = np.array([[0, 1.], [-1., 0]]) @ (b - a)
        ban /= np.linalg.norm(ban)
        ban *= self.orient_edge_control_offset * self.scale
        c1 = a + ban
        c2 = b + ban

        path.cubicTo(QPointF(*c1), QPointF(*c2), self._calc_coord(j))

        self._draw_arrow_at(painter, path, 0.55)
        painter.drawPath(path)

    def _draw_arrow_at(self, painter: QPainter, path: QPainterPath, where: float):
        real_point = path.pointAtPercent(where)
        real_point = np.array([real_point.x(), real_point.y()])
        other_point = path.pointAtPercent(where+0.01)
        other_point = np.array([other_point.x(), other_point.y()])
        delta = other_point - real_point
        delta /= np.linalg.norm(delta)
        delta_perp = np.array([[0, 1.], [-1., 0]]) @ delta

        ts = self.triangle_size * self.scale

        p1 = real_point + delta_perp * ts/2
        p2 = real_point + delta * ts * 1.5
        p3 = real_point - delta_perp * ts/2
        tripath = QPainterPath()
        tripath.moveTo(*p1)
        tripath.lineTo(*p2)
        tripath.lineTo(*p3)
        tripath.lineTo(*p1)

        painter.fillPath(tripath, QBrush(painter.pen().color()))
        painter.drawPath(tripath)

    def _get_edge_color(self, coef: float):
        return QColor(
            int(
                coef * self.max_edge_color.red() +
                (1 - coef) * self.min_edge_color.red()
            ),
            int(
                coef * self.max_edge_color.green() +
                (1 - coef) * self.min_edge_color.green()
            ),
            int(
                coef * self.max_edge_color.blue() +
                (1 - coef) * self.min_edge_color.blue()
            )
        )

    def _set_pen(self, painter: QPainter, mode: int, coef: float = None):
        if mode == 1:
            painter.setPen(QPen(self.default_edge_color, self.scale * self.edge_size))
        elif mode == -1:
            curr_col = self._get_edge_color(coef)
            painter.setPen(QPen(curr_col, self.scale * self.edge_size))
        elif mode == -2:
            painter.setPen(QPen(self.highlight_color, self.scale * (self.edge_size*self.highlight_mul)))


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
        self.open_graph_button = QPushButton(self)

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
        right_layout.addWidget(self.open_graph_button)
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
        self.view.connect_info_field(self.click_info)
        self.random_graph()

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
        self.open_graph_button.setText('Open graph...')
        self.open_graph_button.clicked.connect(self.open_graph)
        self.new_graph_button.setText('Random graph')
        self.new_graph_button.clicked.connect(self.random_graph)

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
        self.view.reset()

    def open_graph(self):
        path = QFileDialog.getOpenFileName(
            self, 'Open graph', '',
            'NumPy pickled graphs (*.npy *.npz)'
        )
        if path[0] != '':
            print(path[0])
            graph = np.load(path[0])
            self._set_new_graph(graph)

    def random_graph(self):
        graph = nx.to_numpy_array(nx.random_geometric_graph(116, 0.1), dtype=float)
        self._set_new_graph(graph)

    def _set_new_graph(self, graph):
        self.graph = graph
        self.view.set_graph(self.graph)
        self.view.set_params(
            ollivier=np.array(rc.calculate_ollivier(self.graph, 0.)),
            forman=np.array(rc.calculate_forman(self.graph))
        )


print('step 1')
app = QApplication(sys.argv)
print('step 2')
window = MainWindow()
print('step 3')
app.exec_()
