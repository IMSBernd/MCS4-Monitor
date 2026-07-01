from collections import defaultdict, deque
from datetime import datetime

import pyqtgraph as pg
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QMainWindow, QPushButton,
                               QPlainTextEdit, QTableWidget, QTableWidgetItem, QTabWidget,
                               QVBoxLayout, QWidget)

from alarms.alarm_manager import AlarmManager
from communication.com_manager import ComManager
from communication.player import TelegramPlayer
from communication.recorder import TelegramRecorder, hex_string
from communication.simulator import MCSSimulator
from communication.telegram_buffer import TelegramBuffer
from protocol.decoder import MCS4Decoder
from sensors.sensor_manager import SensorManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MCS-4 Monitor - Version 0.8 Recorder/Player")
        self.resize(1350, 840)
        self.simulator = MCSSimulator()
        self.com = ComManager()
        self.buffer = TelegramBuffer()
        self.decoder = MCS4Decoder()
        self.sensors = SensorManager(timeout_seconds=3.0)
        self.alarms = AlarmManager()
        self.recorder = TelegramRecorder()
        self.player = TelegramPlayer()
        self.packet_count = 0
        self.byte_count = 0
        self.trend_data = defaultdict(lambda: deque(maxlen=200))
        self.curves = {}
        self._build_ui()
        self.refresh_ports()
        self.sim_timer = QTimer(self); self.sim_timer.timeout.connect(self.sim_tick)
        self.rs_timer = QTimer(self); self.rs_timer.timeout.connect(self.rs_tick)
        self.play_timer = QTimer(self); self.play_timer.timeout.connect(self.play_tick)
        self.diag_timer = QTimer(self); self.diag_timer.timeout.connect(self.update_diagnostics); self.diag_timer.start(1000)

    def _build_ui(self):
        root = QWidget(); layout = QVBoxLayout(root); top = QHBoxLayout()
        self.mode = QComboBox(); self.mode.addItems(["Simulator", "RS422", "Player"])
        self.port_box = QComboBox(); self.refresh_btn = QPushButton("Ports aktualisieren")
        self.start_btn = QPushButton("Start"); self.stop_btn = QPushButton("Stop")
        self.rec_btn = QPushButton("Aufnahme Start"); self.rec_stop_btn = QPushButton("Aufnahme Stop")
        self.status = QLabel("Status: bereit")
        for w in [QLabel("Modus:"), self.mode, QLabel("COM-Port:"), self.port_box, self.refresh_btn, self.start_btn, self.stop_btn, self.rec_btn, self.rec_stop_btn]: top.addWidget(w)
        top.addStretch(); top.addWidget(self.status); layout.addLayout(top)
        tabs = QTabWidget()
        self.table = QTableWidget(0, 9); self.table.setHorizontalHeaderLabels(["ID", "Sensor", "Wert", "Einheit", "Min", "Max", "Status", "Alarm", "Zeit"]); self.table.horizontalHeader().setStretchLastSection(True); tabs.addTab(self.table, "Dashboard")
        self.trend_plot = pg.PlotWidget(); self.trend_plot.setBackground("w"); self.trend_plot.showGrid(x=True, y=True); self.trend_plot.addLegend(); tabs.addTab(self.trend_plot, "Trend")
        self.telegram_log = QPlainTextEdit(); self.telegram_log.setReadOnly(True); tabs.addTab(self.telegram_log, "Telegramme")
        self.decoder_log = QPlainTextEdit(); self.decoder_log.setReadOnly(True); tabs.addTab(self.decoder_log, "Decoder")
        self.alarm_log = QPlainTextEdit(); self.alarm_log.setReadOnly(True); tabs.addTab(self.alarm_log, "Alarme")
        self.diagnostics = QPlainTextEdit(); self.diagnostics.setReadOnly(True); tabs.addTab(self.diagnostics, "Diagnose")
        layout.addWidget(tabs); self.setCentralWidget(root)
        self.refresh_btn.clicked.connect(self.refresh_ports); self.start_btn.clicked.connect(self.start); self.stop_btn.clicked.connect(self.stop)
        self.rec_btn.clicked.connect(self.start_recording); self.rec_stop_btn.clicked.connect(self.stop_recording)

    def refresh_ports(self):
        self.port_box.clear(); ports = ComManager.available_ports()
        if not ports: self.port_box.addItem("Kein COM-Port gefunden", ""); return
        for port, desc in ports: self.port_box.addItem(f"{port} - {desc}", port)

    def start(self):
        self.stop(); self.telegram_log.clear(); self.decoder_log.clear(); self.buffer.clear()
        mode = self.mode.currentText()
        if mode == "Simulator": self.status.setText("Status: Simulator läuft"); self.log("Simulator gestartet"); self.sim_timer.start(250)
        elif mode == "RS422": self.start_rs422()
        else: self.start_player()

    def stop(self):
        self.sim_timer.stop(); self.rs_timer.stop(); self.play_timer.stop()
        if self.com.is_open:
            self.com.close(); self.log("RS422 geschlossen")
        self.status.setText("Status: gestoppt")

    def start_rs422(self):
        port = self.port_box.currentData()
        if not port: self.log("Kein COM-Port ausgewählt"); return
        try:
            self.com.open(port); self.status.setText(f"Status: RS422 verbunden {port}"); self.log(f"RS422 geöffnet: {port}, 38400 Baud, 8O1"); self.rs_timer.start(50)
        except Exception as exc: self.status.setText("Status: RS422 Fehler"); self.log(f"RS422 Fehler: {exc}")

    def start_player(self):
        path = self.player.load_latest()
        if not path: self.log("Keine Aufnahme in recordings gefunden"); return
        self.status.setText(f"Status: Player läuft ({path})"); self.log(f"Player geladen: {path}"); self.play_timer.start(250)

    def start_recording(self):
        path = self.recorder.start(); self.log(f"Aufnahme gestartet: {path}")

    def stop_recording(self):
        self.recorder.stop(); self.log("Aufnahme gestoppt")

    def sim_tick(self): self.handle_bytes(self.simulator.next_bytes(), "RX")

    def rs_tick(self):
        data = self.com.read_available()
        if data: self.handle_bytes(data, "RX")

    def play_tick(self):
        packet = self.player.next_packet()
        if packet: self.handle_bytes(packet, "PLAY")

    def handle_bytes(self, data: bytes, direction: str):
        self.byte_count += len(data); self.telegram_log.appendPlainText(f"{direction} {hex_string(data)}")
        for packet in self.buffer.feed(data):
            self.recorder.write_packet(packet)
            self.handle_packet(packet)

    def handle_packet(self, packet: bytes):
        decoded = self.decoder.decode(packet)
        if decoded is None: return
        sensor = self.sensors.update(decoded); alarm = self.alarms.evaluate(sensor)
        if alarm: self.alarm_log.appendPlainText(alarm)
        self.packet_count += 1
        now = datetime.now().strftime("%H:%M:%S")
        self.decoder_log.appendPlainText(f"{now} CH={decoded.channel} {decoded.name}={decoded.value:.2f} {decoded.unit} SRC={decoded.source} DST={decoded.destination}")
        self.update_dashboard(); self.update_trend(decoded.channel, decoded.value, decoded.name)

    def update_dashboard(self):
        sensors = self.sensors.all(); self.table.setRowCount(len(sensors))
        for row, s in enumerate(sensors):
            values = [str(s["id"]), s["name"], f'{s["value"]:.2f}', s["unit"], f'{s["min"]:.2f}', f'{s["max"]:.2f}', s["status"], s["alarm"], s["last_update"].strftime("%H:%M:%S")]
            for col, text in enumerate(values):
                item = QTableWidgetItem(text)
                if col in (0,2,4,5): item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if s["status"] == "ALARM": item.setBackground(Qt.red); item.setForeground(Qt.white)
                elif s["status"] == "WARNUNG": item.setBackground(Qt.yellow); item.setForeground(Qt.black)
                elif s["status"] == "OFFLINE": item.setBackground(Qt.lightGray); item.setForeground(Qt.black)
                self.table.setItem(row, col, item)

    def update_trend(self, channel, value, name):
        self.trend_data[channel].append(value)
        if channel not in self.curves: self.curves[channel] = self.trend_plot.plot([], [], pen=pg.mkPen(width=2), name=name)
        y = list(self.trend_data[channel]); x = list(range(len(y))); self.curves[channel].setData(x, y)

    def update_diagnostics(self):
        self.update_dashboard()
        self.diagnostics.setPlainText(f"Zeit: {datetime.now():%Y-%m-%d %H:%M:%S}\nModus: {self.mode.currentText()}\nTelegramme dekodiert: {self.packet_count}\nBytes: {self.byte_count}\nCOM-Port: {self.port_box.currentData()}\nRS422 aktiv: {'Ja' if self.com.is_open else 'Nein'}\nAufnahme aktiv: {'Ja' if self.recorder.active else 'Nein'}\nSensoren: {len(self.sensors.all())}\nAktive Alarme: {len(self.alarms.active)}\n")

    def log(self, text): self.telegram_log.appendPlainText(f"LOG {datetime.now():%H:%M:%S} {text}")
    def closeEvent(self, event): self.stop_recording(); self.stop(); event.accept()
