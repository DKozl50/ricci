import sys

import plotly.graph_objects as go

import networkx as nx

import matplotlib.pyplot as plt

from PyQt5.QtWidgets import QMenu, QToolBar, QAction, QHBoxLayout
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow
from PyQt5.QtGui import QPixmap, QImage, QPainter
from PyQt5.QtGui import QIcon


G = nx.random_geometric_graph(200, 0.125)
picname = "graph_pic.png"


def savePicture(g, name):
    nx.draw(g)
    plt.savefig(name)


savePicture(G, picname)


class Window(QMainWindow):
    """Main Window."""
    def __init__(self, parent=None):
        """Initializer."""
        super().__init__(parent)
        self.setWindowTitle("Python Menus Toolbars")
        self.resize(800, 600)
        self.centralWidget = QLabel("Welcome in the graph visualizer!")
        self.centralWidget.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.setCentralWidget(self.centralWidget)
        self._addPic()
        self._createActions()
        self._createMenuBar()
        self._createToolBars()
        # self.loadImage("C:/Users/Lisa/PycharmProjects/Curvature/graph_pic.png")

    def loadImage(self, imagePath):
        ''' To load and display new image.'''
        self.qimage = QImage(imagePath)
        self.qpixmap = QPixmap(self.qlabel_image.size())
        if not self.qimage.isNull():
            # reset Zoom factor and Pan position
            self.zoomX = 1
            self.position = [0, 0]
            self.qimage_scaled = self.qimage.scaled(self.qlabel_image.width(), self.qlabel_image.height(), Qt.KeepAspectRatio)
            self.update()
        else:
            self.statusbar.showMessage('Cannot open this image! Try another one.', 5000)

    def update(self):
        ''' This function actually draws the scaled image to the qlabel_image.
            It will be repeatedly called when zooming or panning.
            So, I tried to include only the necessary operations required just for these tasks.
        '''
        if not self.qimage_scaled.isNull():
            # check if position is within limits to prevent unbounded panning.
            px, py = self.position
            px = min(px, max(0, self.qimage_scaled.width() - self.qlabel_image.width()))
            py = min(py, max(0, self.qimage_scaled.height() - self.qlabel_image.height()))
            self.position = (px, py)

            if self.zoomX == 1:
                self.qpixmap.fill(Qt.white)

            # the act of painting the qpixamp
            painter = QPainter()
            painter.begin(self.qpixmap)
            painter.drawImage(QPoint(0, 0), self.qimage_scaled,
                              QRect(self.position[0], self.position[1],
                                    self.qlabel_image.width(), self.qlabel_image.height()))
            painter.end()

            self.qlabel_image.setPixmap(self.qpixmap)
        else:
            pass

    def _addPic(self):
        self.lb = QLabel(self)
        pixmap = QPixmap("C:/Users/Lisa/PycharmProjects/Curvature/graph_pic.png")
        # height_of_label = 500
        self.lb.move(15, 40)
        self.lb.resize(self.width() - 30, self.height() - 80)
        self.lb.setPixmap(pixmap.scaled(self.lb.size(), Qt.IgnoreAspectRatio))
        self.show()

        # lb = QLabel(self)
        # pixmap = QPixmap("C:/Users/Lisa/PycharmProjects/Curvature/graph_pic.png")
        # height_label = 100
        # lb.resize(self.width(), height_label)
        # lb.setPixmap(pixmap.scaled(lb.size(), Qt.IgnoreAspectRatio))
        # self.centralWidget = lb
        # self.centralWidget.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        # self.setCentralWidget(self.centralWidget)
        # self.show()

    def _createMenuBar(self):
        menuBar = self.menuBar()

        # File menu
        fileMenu = QMenu("File", self)
        menuBar.addMenu(fileMenu)
        fileMenu.addAction(self.newAction)
        fileMenu.addAction(self.openAction)
        fileMenu.addAction(self.saveAction)
        fileMenu.addAction(self.exitAction)
        # Edit menu
        editMenu = menuBar.addMenu("Edit")
        editMenu.addAction(self.copyAction)
        editMenu.addAction(self.pasteAction)
        editMenu.addAction(self.cutAction)
        editMenu.addAction(self.cutAction)
        # Find and Replace submenu in the Edit menu
        findMenu = editMenu.addMenu("Find and Replace")
        findMenu.addAction("Find...")
        findMenu.addAction("Replace...")
        # Help menu
        helpMenu = menuBar.addMenu("Help")
        helpMenu.addAction(self.helpContentAction)
        helpMenu.addAction(self.aboutAction)

    def _createToolBars(self):
        # Using a title
        fileToolBar = self.addToolBar("File")
        # Using a QToolBar object
        editToolBar = QToolBar("Edit", self)
        self.addToolBar(editToolBar)
        # Using a QToolBar object and a toolbar area
        helpToolBar = QToolBar("Help", self)
        self.addToolBar(Qt.LeftToolBarArea, helpToolBar)

    def _createActions(self):
        # Creating action using the first constructor
        self.newAction = QAction(self)
        self.newAction.setText("New")
        # Creating actions using the second constructor
        self.openAction = QAction("Open...", self)
        self.saveAction = QAction("Save", self)
        self.exitAction = QAction("Exit", self)
        self.copyAction = QAction("&Copy", self)
        self.pasteAction = QAction("&Paste", self)
        self.cutAction = QAction("Cut", self)
        self.helpContentAction = QAction("Help Content", self)
        self.aboutAction = QAction("About", self)
        # # File actions
        # self.newAction = QAction(self)
        # self.newAction.setText("&amp;New")
        # self.newAction.setIcon(QIcon(":file-new.svg"))
        # self.openAction = QAction(QIcon(":file-open.svg"), "&amp;Open...", self)
        # self.saveAction = QAction(QIcon(":file-save.svg"), "&amp;Save", self)
        # self.exitAction = QAction("&amp;Exit", self)
        # # Edit actions
        # self.copyAction = QAction(QIcon(":edit-copy.svg"), "&amp;Copy", self)
        # self.pasteAction = QAction(QIcon(":edit-paste.svg"), "&amp;Paste", self)
        # self.cutAction = QAction(QIcon(":edit-cut.svg"), "C&amp;ut", self)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec_())
