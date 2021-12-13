import datetime
import sqlite3
import sys
import threading

from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import Qt, QTime, QTimer, QPoint, QDate, pyqtSignal, QObject, QRect
from PyQt5.QtGui import QPainter, QBrush, QPolygon, QImage
from PyQt5.QtWidgets import QApplication, QMainWindow, QGridLayout, QLabel, QPushButton, QVBoxLayout, \
    QHBoxLayout, QDateTimeEdit, QFileDialog, QScrollArea, QGroupBox, QMessageBox

# инициализируем базу данных
db_connection = sqlite3.connect("clocks.sqlite")
cursor = db_connection.cursor()


class Clock(QtWidgets.QWidget):
    def __init__(self, timezone, parent=None):
        super().__init__(parent)
        # Таймер, для обновления окна
        timer = QTimer(self)
        timer.timeout.connect(self.update)
        timer.start(1000)
        self.timezone = timezone
        self.hourPointer = QtGui.QPolygon([QPoint(6, 7),
                                           QPoint(-6, 7),
                                           QPoint(0, -50)])
        self.minutesPointer = QPolygon([QPoint(6, 7),
                                        QPoint(-6, 7),
                                        QPoint(0, -70)])
        self.bColor = Qt.black

    def paintEvent(self, e):
        painter = QPainter(self)
        rec = min(self.width(), self.height())  # берём меньшую из сторон окна
        # устанавливаем время часов
        delta = datetime.timedelta(hours=self.timezone, minutes=0)
        timeInTimezone = (datetime.datetime.now(datetime.timezone.utc) + delta).time()  # Время в заданное зоне
        tik = QTime(timeInTimezone.hour, timeInTimezone.minute, timeInTimezone.second)

        def drawPointer(color, rotation, pointer):
            # Рисуем стрелку
            painter.setBrush(QBrush(color))
            painter.save()
            painter.rotate(rotation)
            painter.drawConvexPolygon(pointer)
            painter.restore()

        # Инициализируем картинку заднего фона
        a = QImage('clocks.png')
        # Создаем прямоугольник, в который будет вписываться задний фон
        target = QRect(0, 0, rec, rec)
        target.moveCenter(QPoint(int(self.width() / 2), int(self.height() / 2)))  # Двигаем задний фон в центр

        painter.drawImage(target, a)  # отрисовываем задний фон
        # Перемещаем место отрисовки в центр виджета
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(rec / 250, rec / 250)
        painter.setPen(QtCore.Qt.NoPen)
        # Отрисовываем стрелки
        drawPointer(self.bColor, (30 * (tik.hour() + tik.minute() / 60)), self.hourPointer)
        drawPointer(self.bColor, (6 * (tik.minute() + tik.second() / 60)), self.minutesPointer)
        painter.end()


class AddAlarmClockWindow(QtWidgets.QDialog):
    def __init__(self, signal: pyqtSignal, parent=None):
        super().__init__(parent, QtCore.Qt.Window)
        layout = QVBoxLayout()
        self.signal = signal  # Сигнал, для обновления списка будильников на начальном окне
        self.title = QLabel("Добавление будильника")
        self.title.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))
        self.title.setAlignment(Qt.AlignHCenter)
        layout.addWidget(self.title)

        # Строка для выбора даты будильника
        hbox = QHBoxLayout()
        self.label = QLabel("Дата срабатывание будильника")
        self.label.setFont(QtGui.QFont("Arial", 8))
        hbox.addWidget(self.label)
        self.datetime = QDateTimeEdit()
        self.datetime.setDate(QDate.currentDate())
        hbox.addWidget(self.datetime)
        layout.addLayout(hbox)

        # Строка для выбора мелодии будильника
        hbox = QHBoxLayout()
        self.label2 = QLabel("Мелодия будильника")
        self.label2.setFont(QtGui.QFont("Arial", 8))
        hbox.addWidget(self.label2)
        self.fileButton = QPushButton("Выбрать файл")
        self.fileButton.clicked.connect(self.getSound)
        hbox.addWidget(self.fileButton)
        layout.addLayout(hbox)

        # Строка для уведомлений/ошибок
        self.hbox = QHBoxLayout()
        self.fileLabel = QLabel()
        self.fileLabel.setWordWrap(True)
        self.hbox.addWidget(self.fileLabel)
        layout.addLayout(self.hbox)

        # Строка для кнопок
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
        self.output = {}  # Словарь для выходных данных

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


class Communicate(QObject):
    """Класс для обновления списка будильников"""
    closeApp = pyqtSignal()
    alarm = pyqtSignal()


class App(QMainWindow, QObject):
    alarmed = False  # Переменная для единоразового оповещения пользователя
    alarmUpdate = False  # Переменная, оповещающая о том, что данные будильников обновились

    def __init__(self):
        super().__init__()
        uic.loadUi('main.ui', self)
        self.title = 'Test'
        self.left = 500
        self.top = 200
        self.width = 400
        self.height = 400
        # Создаем таблицы в бд
        cursor.execute("""CREATE TABLE IF NOT EXISTS alarms (id INTEGER PRIMARY KEY AUTOINCREMENT 
        NOT NULL UNIQUE, datetime DATETIME NOT NULL, sound STRING NOT NULL);""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS clocks (city STRING NOT NULL, timezone INT NOT NULL);""")
        self.c = Communicate()
        self.c.closeApp.connect(
            lambda: self.updateAlarms(db_connection))  # Подключения сигнала обновления списка будильников
        self.c.alarm.connect(self.alarmGoing)
        self.popup = AddAlarmClockWindow(self.c.closeApp, self)  # Инициализация попапа для добавления будильников
        self.add.triggered.connect(self.addAlarm)  # Привязка кнопки из menubar к вызову функции
        self.InitWindow()
        # Создаем и запускаем поток, отслеживающий ближайший будильник
        thread = threading.Thread(target=self.setAlarm, daemon=True)
        thread.start()
        # Обновляем список будильников
        self.updateAlarms(db_connection)
        self.setWindowTitle('PyQtProject')

    def InitWindow(self):
        """Инициализая окна"""
        grid = QGridLayout()
        l = cursor.execute("""SELECT * FROM clocks""").fetchall()
        print(l)
        for i in range(len(l)):
            w = Clock(l[i][1], self)
            grid.addWidget(w, 0, i)
            p = QPushButton(l[i][0])
            p.setEnabled(False)
            grid.addWidget(p, 1, i)
        self.ClocksBox.setLayout(grid)

        self.formLayout = QGridLayout()
        groupBox = QGroupBox("Будильники")
        groupBox.setStyleSheet('background-color: white;')
        groupBox.setLayout(self.formLayout)
        scroll = QScrollArea()
        scroll.setWidget(groupBox)
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(226)
        self.mainLayout.addWidget(scroll)

    def addAlarm(self):
        # Открываем окно для добавления будильника
        self.popup.show()

    def alarmGoing(self):
        # Открываем окно оповещения о будильнике
        date = cursor.execute("""SELECT sound FROM alarms ORDER BY datetime ASC""").fetchone()
        print(date)
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Будильник")
        msg.setText("Сработал будильник")
        okButton = msg.addButton(QMessageBox.Ok)
        msg.exec()

    def setAlarm(self):

        def getNearestAlarm():
            self.alarmed = False
            conn = sqlite3.connect("clocks.sqlite")
            cursor = conn.cursor()
            date = cursor.execute("""SELECT datetime, sound FROM alarms ORDER BY datetime ASC""").fetchone()
            conn.close()
            return date

        l = getNearestAlarm()
        while True:
            # Проверка, не появились ли новые данные
            if self.alarmUpdate:
                self.alarmUpdate = False
                l = getNearestAlarm()
            if l is not None:
                # Проверка, что нынешнее время совпадает со временем, на которое установлен будильник
                alarmDate = datetime.datetime.strptime(l[0], '%Y-%m-%d %H:%M:%S')
                if alarmDate.date() == datetime.date.today():
                    if alarmDate.time().strftime('%H-%M') == datetime.datetime.strftime(datetime.datetime.now(),
                                                                                        '%H-%M'):
                        if not self.alarmed:
                            # Получаем ближайший будильник
                            self.c.alarm.emit()
                            l = getNearestAlarm()
                            self.alarmed = True
                            # Обновляем список будильников и включаем оповещение
                            self.c.closeApp.emit()

    def updateAlarms(self, db_connect):
        # Очищаем список будильников
        l = db_connect.cursor().execute("""SELECT * FROM alarms""").fetchall()
        for i in l:
            alarmDate = datetime.datetime.strptime(i[1], '%Y-%m-%d %H:%M:%S')
            if datetime.datetime.now() > alarmDate:
                db_connect.cursor().execute(f"""DELETE FROM alarms WHERE id='{i[0]}'""")
        db_connect.commit()
        # l = cursor.execute("""DELETE FROM alarm WHERE """)
        for i in reversed(range(self.formLayout.count())):
            self.formLayout.itemAt(i).widget().setParent(None)
        # Получаем будильники из базы данных
        l = db_connect.cursor().execute("""SELECT datetime, sound FROM alarms ORDER BY datetime DESC""").fetchall()
        self.alarmUpdate = True
        # Добавляем будильники в список
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
