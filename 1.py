import datetime
import math
import sqlite3
import sys

from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import Qt, QTime, QTimer, QPoint, QDate, pyqtSignal, QObject
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QPolygon
from PyQt5.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt5.QtWidgets import QApplication, QMainWindow, QGridLayout, QLabel, QPushButton, QVBoxLayout, \
    QHBoxLayout, QDateTimeEdit, QFileDialog, QScrollArea, QGroupBox

db_connection = sqlite3.connect("clocks.sqlite")  # инициализируем базу данных
cursor = db_connection.cursor()


class Clock(QtWidgets.QWidget):
    L = 12
    r = 20
    DELTA_ANGLE = 2 * math.pi / L

    def __init__(self, parent=None):
        super().__init__(parent)
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
        self.bColor = Qt.green

    def paintEvent(self, e):
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
                # painter.drawText(80, 0, '1')
                painter.drawLine(87, 0, 97, 0)
            painter.rotate(6)

        rect = QtCore.QRectF(0, 0, rec / 100, rec / 100)
        for i in range(self.L):
            j = (i + 2) % self.L + 1
            c = self.center_by_index(i)
            #rect.moveCenter(c)
            painter.setPen(QtGui.QColor("black"))
            painter.drawText(rect, QtCore.Qt.AlignCenter, str(j))

        painter.end()
        self.update()

    def center_by_index(self, index):
        R = min(self.rect().width(), self.rect().height()) / 2
        angle = self.DELTA_ANGLE * index
        center = self.rect().center()
        return center + (R - self.r) * QtCore.QPointF(math.cos(angle), math.sin(angle))


class AddAlarmClockWindow(QtWidgets.QDialog):
    def __init__(self, signal: pyqtSignal, parent=None):
        super().__init__(parent, QtCore.Qt.Window)
        layout = QVBoxLayout()
        self.signal = signal  # Сигнал, для обновления списка будильников на начальном окне
        self.title = QLabel("Добавление будильника")
        self.title.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))
        self.title.setAlignment(Qt.AlignHCenter)
        layout.addWidget(self.title)

        hbox = QHBoxLayout()
        self.label = QLabel("Дата срабатывание будильника")
        self.label.setFont(QtGui.QFont("Arial", 8))
        hbox.addWidget(self.label)
        self.datetime = QDateTimeEdit()
        self.datetime.setDate(QDate.currentDate())
        hbox.addWidget(self.datetime)
        layout.addLayout(hbox)

        hbox = QHBoxLayout()
        self.label2 = QLabel("Мелодия будильника")
        self.label2.setFont(QtGui.QFont("Arial", 8))
        hbox.addWidget(self.label2)
        self.fileButton = QPushButton("Выбрать файл")
        self.fileButton.clicked.connect(self.getSound)
        hbox.addWidget(self.fileButton)
        layout.addLayout(hbox)

        self.hbox = QHBoxLayout()
        self.fileLabel = QLabel()
        self.fileLabel.setWordWrap(True)
        self.hbox.addWidget(self.fileLabel)
        layout.addLayout(self.hbox)

        hbox = QHBoxLayout()
        self.cancel = QPushButton("Отмена")
        self.cancel.clicked.connect(self.hide)
        self.ok = QPushButton("Добавить")
        self.ok.clicked.connect(self.acceptAlarm)
        hbox.addWidget(self.cancel)
        hbox.addWidget(self.ok)
        layout.addLayout(hbox)
        self.setLayout(layout)
        self.setWindowTitle('Добавление будильника')
        self.output = {}

    def getSound(self):
        sound = QFileDialog.getOpenFileName(self, 'Select sound', '', 'Audio Files (*.mp3 *.wav *.ogg)')
        if sound[0]:  # Если выбран файл, то оповещаем пользователя
            self.fileLabel.setText(f"Выбрана мелодия по пути: {sound[0]}")
            self.output['sound'] = sound[0]

    def acceptAlarm(self):
        d = self.datetime.dateTime().toPyDateTime()
        # Проверяем, что все данные корректны
        if d < datetime.datetime.now():
            self.fileLabel.setText("Установленная дата уже прошла")
            return
        try:
            self.output['sound']
        except KeyError:
            self.fileLabel.setText("Не выбрана мелодия")
            return
        self.output['date'] = d
        # Записываем в базу данных
        cursor.execute(
            F"""INSERT INTO alarms(datetime, sound) VALUES('{self.output['date']}', '{self.output['sound']}')""")
        db_connection.commit()
        # Очищаем поля и закрываем окно
        self.datetime.setDate(QDate.currentDate())
        self.datetime.setTime(QTime(0, 0))
        self.fileLabel.clear()
        self.output = {}
        self.close()
        self.signal.emit()


"""Класс для обновления списка будильников"""


class Communicate(QObject):
    closeApp = pyqtSignal()


class App(QMainWindow, QObject):
    def __init__(self):
        super().__init__()
        uic.loadUi('main.ui', self)
        self.title = 'Test'
        self.left = 500
        self.top = 200
        self.width = 400
        self.height = 400
        cursor.execute("""CREATE TABLE IF NOT EXISTS alarms (id INTEGER PRIMARY KEY AUTOINCREMENT 
        NOT NULL UNIQUE, datetime DATETIME NOT NULL, sound STRING NOT NULL);""")
        self.c = Communicate()
        self.c.closeApp.connect(self.updateAlarms)  # Подключения сигнала обновления списка будильников
        self.popup = AddAlarmClockWindow(self.c.closeApp, self)
        self.add.triggered.connect(self.addAlarm)  # Привязка кнопки из menubar к вызову функции
        self.InitWindow()
        self.updateAlarms()
        self.setWindowTitle('PyQtProject')

    def InitWindow(self):
        grid = QGridLayout()
        for i in range(3):
            w = Clock(self)
            grid.addWidget(w, 0, i)
            grid.addWidget(QPushButton("Hello"), 1, i)
        self.ClocksBox.setLayout(grid)

        self.formLayout = QGridLayout()
        groupBox = QGroupBox("Будильники")
        groupBox.setStyleSheet('background-color: white;')

        # for n in range(100):
        #     label1 = QLabel('Slime_%2d' % n)
        #     label1.setStyleSheet("background-color: #DCDCDC; padding: 0; margin: 0;")
        #     label2 = QLabel('lol')
        #     label2.setStyleSheet("background-color: #DCDCDC; padding: 10px 0 10px 0; margin: 0;")
        #     formLayout.addWidget(label1, n, 0)
        #     formLayout.addWidget(label2, n, 1)
        # formLayout.addWidget(label1)
        # formLayout.addRow(label1, label2)

        groupBox.setLayout(self.formLayout)

        scroll = QScrollArea()
        scroll.setWidget(groupBox)
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(226)
        # scroll.setFixedSize(scroll.width(), scroll.height())

        self.mainLayout.addWidget(scroll)
        """"""
        # self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        # self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # self.scroll.setWidgetResizable(True)
        # self.scroll.setWidget(self.TimersBox)

    def addAlarm(self):
        # Открываем окно для добавления будильника
        self.popup.show()

    def setAlarm(self):
        player = QMediaPlayer
        audioOutput = QAudioOutput
        player.setAudioOutput(audioOutput)
        connect(player, SIGNAL(positionChanged(qint64)), self, SLOT(positionChanged(qint64)))
        player.setSource(QUrl.fromLocalFile("/Users/me/Music/coolsong.mp3"))
        audioOutput.setVolume(50)
        player.play()

    def updateAlarms(self):
        for i in reversed(range(self.formLayout.count())):
            self.formLayout.itemAt(i).widget().setParent(None)
        l = cursor.execute("""SELECT datetime, sound FROM alarms ORDER BY datetime DESC""").fetchall()
        for i in range(len(l)):
            label1 = QLabel(l[i][0])
            label1.setStyleSheet("background-color: #DCDCDC; padding: 0; margin: 0;")
            label2 = QLabel(l[i][1])
            label2.setStyleSheet("background-color: #DCDCDC; padding: 10px 0 10px 0; margin: 0;")
            self.formLayout.addWidget(label1, i, 0)
            self.formLayout.addWidget(label2, i, 1)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    a = App()
    a.show()
    sys.exit(app.exec())
