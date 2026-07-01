from collections import defaultdict, deque
from datetime import datetime

import pyqtgraph as pg
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QMainWindow, QPushButton, QPlainTextEdit,
    QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget
)

from alarms.alarm_manager import AlarmManager
from communication.com_manager import ComManager
from communication.simulator import MCSSimulator
from communication.utils import hex_string
from protocol.decoder import MCS4Decoder
from protocol.telegram_buffer import TelegramBuffer
from sensors.sensor_manager import SensorManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MCS-4 Monitor - Version 0.7 modular")
        self.resize(1350, 840)

        self.simulator = MCSSimulator()
        self.com = ComManager()
        self.buffer = TelegramBuffer()
        self.decoder = MCS4Decoder()
        self.sensors = SensorManager()
        self.alarms = AlarmManager()

        self.packet_count = 0
        self.byte_count = 0
        self.trend_data = defaultdict(lambda: deque(maxlen=200))
        self.curves = {}

        self._build_ui()
        self.refresh_ports()

        self.sim_timer = QTimer(self)
        self.sim_timer.timeout.connect(self.read_simulator)
        self.serial_timer = QTimer(self)
        self.serial_timer.timeout.connect(self.read_serial)
        self.diag_timer = QTimer(self)
        self.diag_timer.timeout.connect(self.update_diagnostics)
        self.diag_timer.start(1000)

    def _build_ui(self):
        root = QWidget()
        layout = QVBoxLayout(root)
        top = QHBoxLayout()

        self.mode = QComboBox()
        self.mode.addItems(["Simulator", "RS422"])
        self.port_box = QComboBox()
        self.refresh_btn = QPushButton("Ports aktualisieren")
        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")
        self.status = QLabel("Status: bereit")

        top.addWidget(QLabel("Modus:"))
        top.addWidget(self.mode)
        top.addWidget(QLabel("COM-Port:"))
        top.addWidget(self.port_box)
        top.addWidget(self.refresh_btn)
        top.addWidget(self.start_btn)
        top.addWidget(self.stop_btn)
        top.addStretch()
        top.addWidget(self.status)
        layout.addLayout(top)

        self.tabs = QTabWidget()
        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels(["ID", "Sensor", "Wert", "Einheit", "Min", "Max", "Status", "Alarm", "Zeit"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.tabs.addTab(self.table, "Dashboard")

        self.trend_plot = pg.PlotWidget()
        self.trend_plot.setBackground("w")
        self.trend_plot.showGrid(x=True, y=True)
        self.trend_plot.addLegend()
        self.trend_plot.setLabel("left", "Wert")
        self.trend_plot.setLabel("bottom", "Zeitpunkte")
        self.tabs.addTab(self.trend_plot, "Trend")

        self.telegram_log = QPlainTextEdit(); self.telegram_log.setReadOnly(True)
        self.decoder_log = QPlainTextEdit(); self.decoder_log.setReadOnly(True)
        self.alarm_log = QPlainTextEdit(); self.alarm_log.setReadOnly(True)
        self.diagnostics = QPlainTextEdit(); self.diagnostics.setReadOnly(True)
        self.tabs.addTab(self.telegram_log, "Telegramme")
        self.tabs.addTab(self.decoder_log, "Decoder")
        self.tabs.addTab(self.alarm_log, "Alarme")
        self.tabs.addTab(self.diagnostics, "Diagnose")

        layout.addWidget(self.tabs)
        self.setCentralWidget(root)
        self.refresh_btn.clicked.connect(self.refresh_ports)
        self.start_btn.clicked.connect(self.start)
        self.stop_btn.clicked.connect(self.stop)

    def refresh_ports(self):
        self.port_box.clear()
        ports = ComManager.available_ports()
        if not ports:
            self.port_box.addItem("Kein COM-Port gefunden", "")
            return
        for port, description in ports:
            self.port_box.addItem(f"{port} - {description}", port)

    def start(self):
        self.stop()
        self.telegram_log.clear(); self.decoder_log.clear(); self.alarm_log.clear(); self.buffer.clear()
        if self.mode.currentText() == "Simulator":
            self.status.setText("Status: Simulator läuft")
            self.log("Simulator gestartet")
            self.sim_timer.start(250)
            return
        port = self.port_box.currentData()
        if not port:
            self.status.setText("Status: Kein COM-Port")
            self.log("Kein COM-Port ausgewählt")
            return
        try:
            self.com.open(port)
            self.status.setText(f"Status: RS422 verbunden {port}")
            self.log(f"RS422 geöffnet: {port}, 38400 Baud, 8O1")
            self.serial_timer.start(50)
        except Exception as exc:
            self.status.setText("Status: RS422 Fehler")
            self.log(f"RS422 Fehler: {exc}")

    def stop(self):
        self.sim_timer.stop(); self.serial_timer.stop()
        if self.com.is_open:
            try:
                self.com.close()
                self.log("RS422 geschlossen")
            except Exception as exc:
                self.log(f"Fehler beim Schließen: {exc}")
        self.status.setText("Status: gestoppt")

    def read_simulator(self):
        data = self.simulator.next_bytes()
        self.byte_count += len(data)
        self.telegram_log.appendPlainText(f"RX {hex_string(data)}")
        self.process_bytes(data)

    def read_serial(self):
        try:
            data = self.com.read_available()
            if not data:
                return
            self.byte_count += len(data)
            self.telegram_log.appendPlainText(f"RX {datetime.now():%H:%M:%S.%f}  {hex_string(data)}")
            self.process_bytes(data)
        except Exception as exc:
            self.log(f"Lesefehler RS422: {exc}")
            self.stop()

    def process_bytes(self, data: bytes):
        for packet in self.buffer.feed(data):
            decoded = self.decoder.decode(packet)
            if decoded is None:
                continue
            state, alarm_text, event = self.alarms.evaluate(decoded)
            if event:
                self.alarm_log.appendPlainText(event)
            self.sensors.update(decoded, state, alarm_text)
            self.packet_count += 1
            self.decoder_log.appendPlainText(
                f"{datetime.now():%H:%M:%S} CH={decoded.channel} {decoded.name} = {decoded.value:.2f} {decoded.unit} STATUS={state}"
            )
            self.update_dashboard()
            self.update_trend(decoded.channel, decoded.value, decoded.name)

    def update_dashboard(self):
        sensors = self.sensors.all()
        self.table.setRowCount(len(sensors))
        for row, s in enumerate(sensors):
            values = [
                str(s["id"]), s["name"], f"{s['value']:.2f}", s["unit"],
                f"{s['min']:.2f}", f"{s['max']:.2f}", s["state"], s["alarm"], s["time"]
            ]
            for col, text in enumerate(values):
                item = QTableWidgetItem(text)
                if col in (0, 2, 4, 5):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if s["state"] == "ALARM":
                    item.setBackground(Qt.red); item.setForeground(Qt.white)
                elif s["state"] == "WARNUNG":
                    item.setBackground(Qt.yellow); item.setForeground(Qt.black)
                else:
                    item.setBackground(Qt.white); item.setForeground(Qt.black)
                self.table.setItem(row, col, item)

    def update_trend(self, channel: int, value: float, name: str):
        self.trend_data[channel].append(value)
        if channel not in self.curves:
            self.curves[channel] = self.trend_plot.plot([], [], pen=pg.mkPen(width=2), name=name)
        y = list(self.trend_data[channel])
        self.curves[channel].setData(list(range(len(y))), y)

    def update_diagnostics(self):
        self.diagnostics.setPlainText(
            f"Zeit: {datetime.now():%Y-%m-%d %H:%M:%S}\n"
            f"Modus: {self.mode.currentText()}\n"
            f"Telegramme dekodiert: {self.packet_count}\n"
            f"Bytes empfangen/erzeugt: {self.byte_count}\n"
            f"Aktueller COM-Port: {self.port_box.currentData()}\n"
            f"RS422 aktiv: {'Ja' if self.com.is_open else 'Nein'}\n"
            f"Sensoren im Dashboard: {len(self.sensors.all())}\n"
            f"Aktive Alarme: {len(self.alarms.active)}\n"
        )

    def log(self, text: str):
        self.telegram_log.appendPlainText(f"LOG {datetime.now():%H:%M:%S} {text}")

    def closeEvent(self, event):
        self.stop()
        event.accept()
