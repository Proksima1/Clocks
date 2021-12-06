import sys

from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import Qt, QTime, QTimer, QPoint
from PyQt5.QtGui import QPainter, QPixmap, QColor, QBrush, QPen, QPolygon
from PyQt5.QtWidgets import QApplication, QMainWindow, QGridLayout, QFrame, QLabel, QPushButton


class Clock(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.resize(200, 200)
        timer = QTimer(self)
        timer.timeout.connect(self.update)
        timer.start(1000)
        self.setStyleSheet('QWidget {Background-color: %s}' % QColor('black').name())
        self.setStyleSheet("background : black;")
        self.hPointer = QtGui.QPolygon([QPoint(6, 7),
                                        QPoint(-6, 7),
                                        QPoint(0, -50)])
        self.mPointer = QPolygon([QPoint(6, 7),
                                  QPoint(-6, 7),
                                  QPoint(0, -70)])
        self.sPointer = QPolygon([QPoint(1, 1),
                                  QPoint(-1, 1),
                                  QPoint(0, -90)])
        self.bColor = Qt.green

    def paintEvent(self, e):
        print(e)
        painter = QPainter(self)
        rec = min(self.width(), self.height())
        tik = QTime.currentTime()

        def drawPointer(color, rotation, pointer):
            painter.setBrush(QBrush(color))
            painter.save()
            painter.rotate(rotation)
            painter.drawConvexPolygon(pointer)
            painter.restore()

        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(rec / 250, rec / 250)
        painter.setPen(QtCore.Qt.NoPen)
        drawPointer(self.bColor, (30 * (tik.hour() + tik.minute() / 60)), self.hPointer)
        drawPointer(self.bColor, (6 * (tik.minute() + tik.second() / 60)), self.mPointer)
        painter.setPen(QPen(self.bColor))
        for i in range(0, 60):
            if (i % 5) == 0:
                #painter.drawText()
                painter.drawLine(87, 0, 97, 0)
            painter.rotate(6)
        painter.end()
        self.update()


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('main.ui', self)
        self.title = 'Test'
        self.left = 500
        self.top = 200
        self.width = 400
        self.height = 400
        #self.InitWindow()
        # grid_layout = QGridLayout(self)
        # self.setLayout(grid_layout)
        # grid_layout.setSpacing(0)
        # for x in range(3):
        #     for y in range(3):
        #         button = QPushButton(str(str(3 * x + y)))
        #         grid_layout.addWidget(button, x, y)
        # grid_layout.setColumnStretch(0, 1)
        # grid_layout.setColumnStretch(4, 1)
        # grid_layout.setRowStretch(0, 1)
        # grid_layout.setRowStretch(4, 1)
        grid = QGridLayout()
        for i in range(3):
            w = Clock(self)
            grid.addWidget(w, 0, i)
            grid.addWidget(QPushButton("Hello"), 1, i)
        self.ClocksBox.setLayout(grid)
        self.setWindowTitle('Basic Grid Layout')

    def InitWindow(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        grid = QGridLayout()
        self.setLayout(grid)
        #w = W(self)
        #grid.addWidget(w, 0, 0)
        grid.addWidget(QPushButton("Hello"), 1, 0, -1, 1)
        #w2 = W(self)
        #grid.addWidget(w2, 1, 0)
        #frame2 = Frame(self)
        #grid.addWidget(frame2, 1, 0)
        #grid.addWidget(QLabel("Hello"), 1, 2)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    a = App()
    a.show()
    sys.exit(app.exec())
