import sys

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import QPoint, QTimer, Qt, QRect
from PyQt5.QtGui import QBrush, QPolygon, QPainter, QPen, QImage
from PyQt5.QtWidgets import QApplication


class Clock(QtWidgets.QWidget):
    L = 12
    r = 20

    def __init__(self, parent=None):
        super().__init__(parent)
        timer = QTimer(self)
        timer.timeout.connect(self.update)
        timer.start(1000)

        self.hPointer = QtGui.QPolygon([QPoint(6, 7),
                                        QPoint(-6, 7),
                                        QPoint(0, -50)])
        self.mPointer = QPolygon([QPoint(6, 7),
                                  QPoint(-6, 7),
                                  QPoint(0, -70)])

        self.bColor = Qt.green

    def paintEvent(self, e):
        painter = QPainter(self)
        rec = min(self.width(), self.height())  # берём меньшую из сторон окна

        def drawPointer(color, rotation, pointer):
            painter.setBrush(QBrush(color))
            painter.save()
            painter.rotate(rotation)
            painter.drawConvexPolygon(pointer)
            painter.restore()

        painter.setRenderHint(QPainter.Antialiasing)
        a = QImage('clocks.png')
       # a.scaled(self.rect().size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        target = QRect(0, 0, rec, rec)
        target.moveCenter(QPoint(int(self.width() / 2), int(self.height() / 2)))
        painter.drawRect(target)
        painter.drawImage(target, a)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.drawEllipse(1, 1, 1, 1)
        painter.scale(rec / 250, rec / 250)
        painter.setPen(QPen(self.bColor))
        for i in range(0, 60):
            if (i % 5) == 0:
                painter.drawLine(87, 0, 97, 0)
            painter.rotate(6)

        painter.end()
        self.update()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    clock = Clock()
    clock.show()
    sys.exit(app.exec_())
