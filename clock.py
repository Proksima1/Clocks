import sys
import math
from PyQt5 import QtCore, QtGui, QtWidgets


class ClockWidget(QtWidgets.QWidget):
    L = 12
    r = 40
    DELTA_ANGLE = 2 * math.pi / L
    current_index = 9

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        rect = QtCore.QRectF(0, 0, self.r, self.r)
        # !!!
        for i in range(self.L):
            j = (i + 2) % self.L + 1
            c = self.center_by_index(i)
            rect.moveCenter(c)
            painter.setPen(QtGui.QColor("black"))
            painter.drawText(rect, QtCore.Qt.AlignCenter, str(j))

    def center_by_index(self, index):
        R = min(self.rect().width(), self.rect().height()) / 2
        angle = self.DELTA_ANGLE * index
        center = self.rect().center()
        return center + (R - self.r) * QtCore.QPointF(math.cos(angle), math.sin(angle))


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    view = ClockWidget()
    view.resize(400, 400)
    view.show()
    sys.exit(app.exec_())