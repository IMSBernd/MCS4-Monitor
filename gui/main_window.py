from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QPlainTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.alarm_manager import AlarmManager
from core.config import AppConfig
from core.sensor_manager import SensorManager
from core.serial_driver import SerialDriver
from core.simulator import MCSSimulator
from database.history import HistoryDatabase
from model.packet import RawPacket
from protocol.mcs4_decoder import MCS4Decoder
from protocol.packet_reader import PacketReader
from protocol.parser import PacketParser, PacketParseError


class MainWindow(QMainWindow):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        self.setWindowTitle(f"{config.app_name} - Version 0.1")
        self.resize(1200, 760)

        self.reader = PacketReader(config.packet.sync_byte, config.packet.length)
        self.parser = PacketParser(config.packet.sync_byte, config.packet.length)
        self.decoder = MCS4Decoder()
        self.sensors = SensorManager()
        self.alarms = AlarmManager()
        self.history = HistoryDatabase(config.database.path)
        self.simulator: MCSSimulator | None = None
        self.serial_driver: SerialDriver | None = None
        self.packet_counter = 0
        self.error_counter = 0

        self._build_ui()
        self._refresh_ports()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_diagnostics)
        self._timer.start(1000)

    def _build_ui(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)

        top = QHBoxLayout()
        self.mode_box = QComboBox()
        self.mode_box.addItems(["Simulator", "RS422"])
        self.port_box = QComboBox()
        self.refresh_button = QPushButton("Ports aktualisieren")
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.status_label = QLabel("Status: bereit")
        top.addWidget(QLabel("Modus:"))
        top.addWidget(self.mode_box)
        top.addWidget(QLabel("COM-Port:"))
        top.addWidget(self.port_box)
        top.addWidget(self.refresh_button)
        top.addWidget(self.start_button)
        top.addWidget(self.stop_button)
        top.addStretch(1)
        top.addWidget(self.status_label)
        layout.addLayout(top)

        tabs = QTabWidget()
        self.sensor_table = QTableWidget(0, 6)
        self.sensor_table.setHorizontalHeaderLabels(["ID", "Sensor", "Wert", "Einheit", "Status", "Zeit"])
        self.sensor_table.horizontalHeader().setStretchLastSection(True)
        tabs.addTab(self.sensor_table, "Dashboard")

        self.telegram_log = QPlainTextEdit()
        self.telegram_log.setReadOnly(True)
        tabs.addTab(self.telegram_log, "Telegramme")

        self.alarm_log = QPlainTextEdit()
        self.alarm_log.setReadOnly(True)
        tabs.addTab(self.alarm_log, "Alarme")

        self.diagnostics = QPlainTextEdit()
        self.diagnostics.setReadOnly(True)
        tabs.addTab(self.diagnostics, "Diagnose")

        layout.addWidget(tabs)
        self.setCentralWidget(root)

        self.refresh_button.clicked.connect(self._refresh_ports)
        self.start_button.clicked.connect(self.start_acquisition)
        self.stop_button.clicked.connect(self.stop_acquisition)

    def _refresh_ports(self) -> None:
        self.port_box.clear()
        ports = SerialDriver.available_ports()
        if not ports:
            self.port_box.addItem("Kein COM-Port gefunden", "")
            return
        for port, description in ports:
            self.port_box.addItem(f"{port} - {description}", port)

    def start_acquisition(self) -> None:
        self.stop_acquisition()
        mode = self.mode_box.currentText()
        if mode == "Simulator":
            self.simulator = MCSSimulator()
            self.simulator.on_data = self._on_bytes_received
            self.simulator.on_log = self._log
            self.simulator.start()
            self.status_label.setText("Status: Simulator läuft")
        else:
            port = self.port_box.currentData()
            try:
                self.serial_driver = SerialDriver(
                    port=port,
                    baudrate=self.config.serial.baudrate,
                    bytesize=self.config.serial.bytesize,
                    parity=self.config.serial.parity,
                    stopbits=self.config.serial.stopbits,
                    timeout=self.config.serial.timeout,
                )
                self.serial_driver.on_data = self._on_bytes_received
                self.serial_driver.on_log = self._log
                self.serial_driver.connect()
                self.status_label.setText(f"Status: verbunden mit {port}")
            except Exception as exc:
                self.status_label.setText("Status: Fehler")
                self._log(f"Verbindungsfehler: {exc}")

    def stop_acquisition(self) -> None:
        if self.simulator:
            self.simulator.stop()
            self.simulator = None
        if self.serial_driver:
            self.serial_driver.disconnect()
            self.serial_driver = None
        self.status_label.setText("Status: gestoppt")

    def _on_bytes_received(self, data: bytes) -> None:
        packets = self.reader.feed(data)
        for raw in packets:
            self.telegram_log.appendPlainText(f"RX {raw.hex()}")
            try:
                packet = self.parser.parse(raw)
                decoded = self.decoder.decode(packet)
                sensor = self.sensors.update_from_decoded(decoded)
                self.history.insert_sensor(sensor)
                self.packet_counter += 1
                for alarm in self.alarms.evaluate(sensor):
                    state = "AKTIV" if alarm.active else "INAKTIV"
                    self.alarm_log.appendPlainText(f"{alarm.timestamp:%H:%M:%S} [{state}] {alarm.text}")
                self._update_sensor_table()
            except PacketParseError as exc:
                self.error_counter += 1
                self._log(f"Parserfehler: {exc}")

    def _update_sensor_table(self) -> None:
        sensors = self.sensors.all_sensors()
        self.sensor_table.setRowCount(len(sensors))
        for row, sensor in enumerate(sensors):
            values = [
                str(sensor.sensor_id),
                sensor.name,
                f"{sensor.value:.2f}",
                sensor.unit,
                sensor.status_text,
                sensor.last_update.strftime("%H:%M:%S") if sensor.last_update else "-",
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col in (0, 2):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.sensor_table.setItem(row, col, item)

    def _update_diagnostics(self) -> None:
        active_alarms = self.alarms.active_alarms()
        text = (
            f"Zeit: {datetime.now():%Y-%m-%d %H:%M:%S}\n"
            f"Empfangene Telegramme: {self.packet_counter}\n"
            f"Parserfehler: {self.error_counter}\n"
            f"Sensoren: {len(self.sensors.all_sensors())}\n"
            f"Aktive Alarme: {len(active_alarms)}\n"
        )
        self.diagnostics.setPlainText(text)

    def _log(self, message: str) -> None:
        self.telegram_log.appendPlainText(f"LOG {datetime.now():%H:%M:%S} {message}")
