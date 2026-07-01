from __future__ import annotations
from collections import deque

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QMainWindow,
    QPushButton, QPlainTextEdit, QTableWidget, QTableWidgetItem, QTabWidget,
    QVBoxLayout, QWidget, QMessageBox
)
import pyqtgraph as pg

from core.com_manager import ComManager, ComPortInfo
from core.events import AppEvents
from core.simulator import EngineSimulator
from core.serial_driver import SerialDriver
from model.sensor import Sensor
from model.telegram import Telegram


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MCS-4 Professional Monitor - v0.5")
        self.resize(1250, 760)

        self.events = AppEvents()
        self.com_manager = ComManager()
        self.simulator = EngineSimulator(interval_s=0.25)
        self.serial_driver: SerialDriver | None = None

        self.sensor_rows: dict[int, int] = {}
        self.trend_data: dict[int, deque] = {}
        self.trend_curves: dict[int, object] = {}
        self.sample_index = 0

        self._build_ui()
        self._wire_events()
        self.refresh_ports()

    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)

        header = QHBoxLayout()
        self.status_label = QLabel("Status: Bereit")
        self.status_label.setStyleSheet("font-weight: bold;")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Simulator", "RS422"])
        self.port_combo = QComboBox()
        self.refresh_btn = QPushButton("Ports aktualisieren")
        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)

        header.addWidget(QLabel("Modus:"))
        header.addWidget(self.mode_combo)
        header.addWidget(QLabel("COM-Port:"))
        header.addWidget(self.port_combo, 1)
        header.addWidget(self.refresh_btn)
        header.addWidget(self.start_btn)
        header.addWidget(self.stop_btn)
        header.addWidget(self.status_label, 1)
        root.addLayout(header)

        tabs = QTabWidget()
        tabs.addTab(self._build_dashboard_tab(), "Dashboard")
        tabs.addTab(self._build_telegram_tab(), "Telegramme")
        tabs.addTab(self._build_diagnostics_tab(), "Diagnose")
        root.addWidget(tabs, 1)
        self.setCentralWidget(central)

    def _build_dashboard_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.sensor_table = QTableWidget(0, 5)
        self.sensor_table.setHorizontalHeaderLabels(["Sensor", "Wert", "Einheit", "Grenzen", "Status"])
        self.sensor_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.sensor_table, 1)

        self.plot = pg.PlotWidget(title="Live-Trend")
        self.plot.setLabel("left", "Wert")
        self.plot.setLabel("bottom", "Samples")
        self.plot.addLegend()
        layout.addWidget(self.plot, 2)
        return tab

    def _build_telegram_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.telegram_text = QPlainTextEdit()
        self.telegram_text.setReadOnly(True)
        self.telegram_text.setMaximumBlockCount(2000)
        layout.addWidget(self.telegram_text)
        return tab

    def _build_diagnostics_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        box = QGroupBox("Kommunikationsdiagnose")
        grid = QGridLayout(box)
        self.diag_labels: dict[str, QLabel] = {}
        for row, key in enumerate(["Quelle", "Telegramme/s", "Telegramme", "Bytes", "CRC-Fehler", "Timeouts"]):
            grid.addWidget(QLabel(key + ":"), row, 0)
            value = QLabel("-")
            self.diag_labels[key] = value
            grid.addWidget(value, row, 1)
        layout.addWidget(box)
        layout.addStretch(1)
        return tab

    def _wire_events(self) -> None:
        self.refresh_btn.clicked.connect(self.refresh_ports)
        self.start_btn.clicked.connect(self.start)
        self.stop_btn.clicked.connect(self.stop)
        self.events.sensor_updated.connect(self._on_sensor_updated)
        self.events.telegram_received.connect(self._on_telegram_received)
        self.events.status_changed.connect(self._on_status_changed)
        self.events.diagnostics_changed.connect(self._on_diagnostics_changed)

        self.simulator.on_sensor = lambda s: self.events.sensor_updated.emit(s)
        self.simulator.on_telegram = lambda t: self.events.telegram_received.emit(t)
        self.simulator.on_diagnostics = lambda d: self.events.diagnostics_changed.emit(d)

    def refresh_ports(self) -> None:
        self.port_combo.clear()
        ports = self.com_manager.list_ports()
        if not ports:
            self.port_combo.addItem("Keine COM-Ports gefunden", None)
            self.status_label.setText("Status: Keine COM-Ports gefunden")
            return
        for port in ports:
            label = port.display_name
            if port.is_likely_exsys:
                label = "★ " + label
            self.port_combo.addItem(label, port)
        self.status_label.setText(f"Status: {len(ports)} COM-Port(s) gefunden")

    def start(self) -> None:
        mode = self.mode_combo.currentText()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        if mode == "Simulator":
            self.simulator.start()
            self.events.status_changed.emit("Simulator läuft")
            return

        port: ComPortInfo | None = self.port_combo.currentData()
        if port is None:
            QMessageBox.warning(self, "Kein COM-Port", "Bitte zuerst einen COM-Port auswählen.")
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            return
        try:
            self.serial_driver = SerialDriver(port.device)
            self.serial_driver.on_bytes = lambda t: self.events.telegram_received.emit(t)
            self.serial_driver.on_status = lambda s: self.events.status_changed.emit(s)
            self.serial_driver.on_diagnostics = lambda d: self.events.diagnostics_changed.emit(d)
            self.serial_driver.start()
        except Exception as exc:
            QMessageBox.critical(self, "Verbindungsfehler", str(exc))
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)

    def stop(self) -> None:
        self.simulator.stop()
        if self.serial_driver:
            self.serial_driver.stop()
            self.serial_driver = None
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.events.status_changed.emit("Gestoppt")

    def _on_status_changed(self, text: str) -> None:
        self.status_label.setText("Status: " + text)

    def _on_sensor_updated(self, sensor: Sensor) -> None:
        if sensor.sensor_id not in self.sensor_rows:
            row = self.sensor_table.rowCount()
            self.sensor_table.insertRow(row)
            self.sensor_rows[sensor.sensor_id] = row
            self.trend_data[sensor.sensor_id] = deque(maxlen=300)
            self.trend_curves[sensor.sensor_id] = self.plot.plot([], [], name=sensor.name)
        row = self.sensor_rows[sensor.sensor_id]
        status = "ALARM" if sensor.is_alarm else "OK"
        values = [
            sensor.name,
            f"{sensor.value:.2f}" if isinstance(sensor.value, float) else str(sensor.value),
            sensor.unit,
            f"{sensor.minimum} ... {sensor.maximum}",
            status,
        ]
        for col, value in enumerate(values):
            item = QTableWidgetItem(value)
            if col == 4:
                item.setTextAlignment(Qt.AlignCenter)
                item.setBackground(Qt.red if status == "ALARM" else Qt.green)
            self.sensor_table.setItem(row, col, item)

        self.sample_index += 1
        self.trend_data[sensor.sensor_id].append((self.sample_index, float(sensor.value)))
        x = [p[0] for p in self.trend_data[sensor.sensor_id]]
        y = [p[1] for p in self.trend_data[sensor.sensor_id]]
        self.trend_curves[sensor.sensor_id].setData(x, y)

    def _on_telegram_received(self, telegram: Telegram) -> None:
        line = f"{telegram.timestamp:%H:%M:%S.%f}  {telegram.source:<6}  RX  {telegram.hex_string}"
        self.telegram_text.appendPlainText(line)

    def _on_diagnostics_changed(self, data: dict) -> None:
        for key, label in self.diag_labels.items():
            if key in data:
                label.setText(str(data[key]))

    def closeEvent(self, event) -> None:
        self.stop()
        event.accept()
