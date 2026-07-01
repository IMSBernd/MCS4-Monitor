from __future__ import annotations

import sys
from datetime import datetime

from PySide6.QtCore import QTimer
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

from communication.recorder import TelegramRecorder
from communication.serial_manager import SerialManager
from communication.simulator import MCSSimulator
from protocol.mcs4_parser import MCS4Parser
from protocol.telegram_buffer import TelegramBuffer


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MCS-4 Monitor - Version 0.5")
        self.resize(1180, 760)

        self.simulator = MCSSimulator()
        self.serial = SerialManager()
        self.buffer = TelegramBuffer()
        self.parser = MCS4Parser()
        self.recorder = TelegramRecorder()

        self.packet_count = 0
        self.byte_count = 0
        self.parse_errors = 0
        self.sensors = {}

        self._build_ui()
        self.refresh_ports()

        self.sim_timer = QTimer(self)
        self.sim_timer.timeout.connect(self._simulator_tick)

        self.serial_timer = QTimer(self)
        self.serial_timer.timeout.connect(self._serial_tick)

        self.diag_timer = QTimer(self)
        self.diag_timer.timeout.connect(self._update_diagnostics)
        self.diag_timer.start(1000)

    def _build_ui(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)

        top = QHBoxLayout()
        self.mode = QComboBox()
        self.mode.addItems(["Simulator", "RS422"])
        self.port_box = QComboBox()
        self.refresh_btn = QPushButton("Ports aktualisieren")
        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")
        self.record_btn = QPushButton("Aufnahme Start")
        self.status = QLabel("Status: bereit")

        top.addWidget(QLabel("Modus:"))
        top.addWidget(self.mode)
        top.addWidget(QLabel("COM-Port:"))
        top.addWidget(self.port_box)
        top.addWidget(self.refresh_btn)
        top.addWidget(self.start_btn)
        top.addWidget(self.stop_btn)
        top.addWidget(self.record_btn)
        top.addStretch()
        top.addWidget(self.status)
        layout.addLayout(top)

        self.tabs = QTabWidget()

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "Sensor", "Wert", "Einheit", "Status", "Zeit"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.tabs.addTab(self.table, "Dashboard")

        self.telegram_log = QPlainTextEdit()
        self.telegram_log.setReadOnly(True)
        self.tabs.addTab(self.telegram_log, "Telegramme")

        self.decoded_log = QPlainTextEdit()
        self.decoded_log.setReadOnly(True)
        self.tabs.addTab(self.decoded_log, "Decoder")

        self.diagnostics = QPlainTextEdit()
        self.diagnostics.setReadOnly(True)
        self.tabs.addTab(self.diagnostics, "Diagnose")

        layout.addWidget(self.tabs)
        self.setCentralWidget(root)

        self.refresh_btn.clicked.connect(self.refresh_ports)
        self.start_btn.clicked.connect(self.start)
        self.stop_btn.clicked.connect(self.stop)
        self.record_btn.clicked.connect(self.toggle_recording)

    def refresh_ports(self) -> None:
        self.port_box.clear()
        ports = SerialManager.available_ports()
        if not ports:
            self.port_box.addItem("Kein COM-Port gefunden", "")
            return
        for port, desc in ports:
            self.port_box.addItem(f"{port} - {desc}", port)

    def start(self) -> None:
        self.stop(clear_status=False)
        self.telegram_log.clear()
        self.decoded_log.clear()
        self.buffer.clear()

        if self.mode.currentText() == "Simulator":
            self.status.setText("Status: Simulator läuft")
            self._log("Simulator gestartet")
            self.sim_timer.start(250)
            return

        port = self.port_box.currentData()
        if not port:
            self.status.setText("Status: Kein COM-Port")
            self._log("Kein COM-Port ausgewählt")
            return

        try:
            self.serial.open(port)
            self.status.setText(f"Status: RS422 verbunden {port}")
            self._log(f"RS422 geöffnet: {port}, 38400 Baud, 8O1")
            self.serial_timer.start(50)
        except Exception as exc:
            self.status.setText("Status: RS422 Fehler")
            self._log(f"RS422 Fehler: {exc}")

    def stop(self, clear_status: bool = True) -> None:
        self.sim_timer.stop()
        self.serial_timer.stop()
        if self.serial.is_open:
            self.serial.close()
            self._log("RS422 geschlossen")
        if clear_status:
            self.status.setText("Status: gestoppt")

    def toggle_recording(self) -> None:
        if self.recorder.active:
            self.recorder.stop()
            self.record_btn.setText("Aufnahme Start")
            self._log("Aufnahme gestoppt")
            return
        path = self.recorder.start()
        self.record_btn.setText("Aufnahme Stop")
        self._log(f"Aufnahme gestartet: {path}")

    def _simulator_tick(self) -> None:
        data = self.simulator.next_bytes()
        self._process_bytes(data, source="SIM")

    def _serial_tick(self) -> None:
        try:
            data = self.serial.read_available()
            if data:
                self._process_bytes(data, source="RS422")
        except Exception as exc:
            self._log(f"RS422 Lesefehler: {exc}")
            self.stop()

    def _process_bytes(self, data: bytes, source: str) -> None:
        self.byte_count += len(data)
        if self.recorder.active:
            self.recorder.write(data)
        telegrams = self.buffer.feed(data)
        if not telegrams and data:
            self.telegram_log.appendPlainText(f"{source} RAW {self._hex(data)}")
            return

        for telegram in telegrams:
            self.packet_count += 1
            self.telegram_log.appendPlainText(f"{source} RX {telegram.hex()}")
            try:
                packet = self.parser.parse_packet(telegram.data, telegram.timestamp)
                sensor = self.parser.decode_sensor(packet)
                self.sensors[sensor.sensor_id] = sensor
                self.decoded_log.appendPlainText(
                    f"{sensor.timestamp:%H:%M:%S} Sensor {sensor.sensor_id}: "
                    f"{sensor.name} = {sensor.value:.2f} {sensor.unit}"
                )
            except Exception as exc:
                self.parse_errors += 1
                self._log(f"Parserfehler: {exc}")
        self._update_table()

    def _update_table(self) -> None:
        values = [self.sensors[k] for k in sorted(self.sensors)]
        self.table.setRowCount(len(values))
        for row, sensor in enumerate(values):
            status = "FEHLER" if sensor.fault else "OK"
            row_values = [
                str(sensor.sensor_id),
                sensor.name,
                f"{sensor.value:.2f}",
                sensor.unit,
                status,
                sensor.timestamp.strftime("%H:%M:%S"),
            ]
            for col, text in enumerate(row_values):
                self.table.setItem(row, col, QTableWidgetItem(text))

    def _update_diagnostics(self) -> None:
        self.diagnostics.setPlainText(
            f"Zeit: {datetime.now():%Y-%m-%d %H:%M:%S}\n"
            f"Modus: {self.mode.currentText()}\n"
            f"Telegramme erkannt: {self.packet_count}\n"
            f"Bytes empfangen/erzeugt: {self.byte_count}\n"
            f"Parserfehler: {self.parse_errors}\n"
            f"Sensoren: {len(self.sensors)}\n"
            f"COM-Port: {self.port_box.currentData()}\n"
            f"RS422 aktiv: {'Ja' if self.serial.is_open else 'Nein'}\n"
            f"Aufnahme aktiv: {'Ja' if self.recorder.active else 'Nein'}\n"
        )

    def _log(self, text: str) -> None:
        self.telegram_log.appendPlainText(f"LOG {datetime.now():%H:%M:%S} {text}")

    def _hex(self, data: bytes) -> str:
        return " ".join(f"{b:02X}" for b in data)

    def closeEvent(self, event) -> None:
        self.stop()
        self.recorder.stop()
        event.accept()
