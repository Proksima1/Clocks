import sys
from datetime import datetime
from PyQt5.QtGui import QColor, QPalette, QBrush, QPixmap, \
    QPolygon, QPainter
from PyQt5.QtCore import QPoint, QTimer, Qt
from PyQt5.QtWidgets import QWidget, QApplication, QAction


class Clock(QWidget):
    def __init__(self):
        super().__init__()

        pixmap = QPixmap("clock.png").scaled(self.rect().size() / 2,
                                             Qt.KeepAspectRatio, Qt.FastTransformation)
        pal = self.palette()
        pal.setBrush(QPalette.Normal, QPalette.Window, QBrush(pixmap))
        pal.setBrush(QPalette.Inactive, QPalette.Window, QBrush(pixmap))
        self.setPalette(pal)

        self.checktime()

        self.hourColor = QColor(127, 0, 127)
        self.minuteColor = QColor(0, 127, 127, 191)
        self.secondColor = QColor(127, 127, 0, 120)

        self.initUI()

        self.setContextMenuPolicy(Qt.ActionsContextMenu)

        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update)
        self.timer.start()

    def handChange(self):
        self.side = min(self.width(), self.height())
        self.hand = (max(self.side / 200, 4), max(self.side / 100, 8), max(self.side / 40, 30))
        self.hourHand = QPolygon([
            QPoint(self.hand[0], self.hand[1]),
            QPoint(-self.hand[0], self.hand[1]),
            QPoint(0, -self.hand[2])
        ])
        self.minuteHand = QPolygon([
            QPoint(self.hand[0], self.hand[1]),
            QPoint(-self.hand[0], self.hand[1]),
            QPoint(0, -self.hand[2] * 1.6)
        ])
        self.secondHand = QPolygon([
            QPoint(self.hand[0], self.hand[1]),
            QPoint(-self.hand[0], self.hand[1]),
            QPoint(0, -self.hand[2] * 1.6 * 1.6)
        ])

    def initUI(self):
        self.handChange()

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        self.draw(event, painter)
        painter.end()

    def draw(self, event, painter):
        self.checktime()
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(self.side / 200.0, self.side / 200.0)

        painter.setPen(Qt.NoPen)
        painter.setBrush(self.hourColor)
        painter.save()
        painter.rotate(30.0 * ((self.time.hour + self.time.minute / 60.0)))
        painter.drawConvexPolygon(self.hourHand)
        painter.restore()

        painter.setPen(Qt.NoPen)
        painter.setBrush(self.minuteColor)
        painter.save()

        painter.rotate(6.0 * ((self.time.minute + (self.time.second) / 60.0)))
        painter.drawConvexPolygon(self.minuteHand)
        painter.restore()

        painter.setPen(Qt.NoPen)
        painter.setBrush(self.secondColor)
        painter.save()
        painter.rotate(6.0 * (self.time.second))
        painter.drawConvexPolygon(self.secondHand)
        painter.restore()

    def checktime(self):
        self.time = datetime.now()
        self.hour = self.time.hour
        self.minute = self.time.minute
        self.second = self.time.second

    # Перетаскивание окна
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self.dragPos)
            event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragPos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    clock = Clock()
    clock.show()
    sys.exit(app.exec_())