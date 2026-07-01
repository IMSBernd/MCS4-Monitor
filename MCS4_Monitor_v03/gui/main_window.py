from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime

import pyqtgraph as pg
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QPlainTextEdit,
    QSplitter,
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
from core.com_port_manager import ComPortManager
from core.simulator import MCSSimulator
from database.history import HistoryDatabase
from protocol.mcs4_decoder import MCS4Decoder
from protocol.packet_reader import PacketReader
from protocol.parser import PacketParser, PacketParseError


class MainWindow(QMainWindow):
    """Hauptfenster der MCS-4 Diagnose-Software.

    Version 0.3 erweitert die bisherige COM-Port-Grundlage um ein echtes Live-
    Dashboard mit Trendgrafik und Alarmübersicht. Die MCS-4-Bitdetails bleiben
    weiterhin sauber in protocol/mcs4_decoder.py gekapselt.
    """

    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        self.setWindowTitle(f"{config.app_name} - Version 0.3")
        self.resize(1280, 820)

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
        self.byte_counter = 0
        self.connection_started_at: datetime | None = None
        self.trend_history: dict[int, deque[float]] = defaultdict(lambda: deque(maxlen=240))
        self.trend_curves: dict[int, pg.PlotDataItem] = {}

        self._build_ui()
        self._refresh_ports()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_diagnostics)
        self._timer.start(1000)

    def _build_ui(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)

        header = QHBoxLayout()
        self.mode_box = QComboBox()
        self.mode_box.addItems(["Simulator", "RS422"])
        self.port_box = QComboBox()
        self.refresh_button = QPushButton("Ports aktualisieren")
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.status_label = QLabel("Status: bereit")
        self.adapter_label = QLabel("Adapter: -")
        self.status_label.setMinimumWidth(180)
        header.addWidget(QLabel("Modus:"))
        header.addWidget(self.mode_box)
        header.addWidget(QLabel("COM-Port:"))
        header.addWidget(self.port_box, 1)
        header.addWidget(self.refresh_button)
        header.addWidget(self.start_button)
        header.addWidget(self.stop_button)
        header.addStretch(1)
        header.addWidget(self.adapter_label)
        header.addWidget(self.status_label)
        layout.addLayout(header)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_dashboard_tab(), "Dashboard")
        self.tabs.addTab(self._create_telegram_tab(), "Telegramme")
        self.tabs.addTab(self._create_alarm_tab(), "Alarme")
        self.tabs.addTab(self._create_diagnostics_tab(), "Diagnose")
        layout.addWidget(self.tabs)
        self.setCentralWidget(root)

        self.refresh_button.clicked.connect(self._refresh_ports)
        self.start_button.clicked.connect(self.start_acquisition)
        self.stop_button.clicked.connect(self.stop_acquisition)

    def _create_dashboard_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        cards = QGridLayout()
        self.card_values: dict[int, QLabel] = {}
        self.card_status: dict[int, QLabel] = {}
        names = [
            (1, "Öltemperatur"),
            (2, "Öldruck"),
            (3, "Drehzahl"),
            (4, "Kühlwasser"),
            (5, "Abgastemperatur"),
            (6, "Ladedruck"),
        ]
        for index, (sensor_id, name) in enumerate(names):
            box = QGroupBox(name)
            box_layout = QVBoxLayout(box)
            value = QLabel("--")
            value.setAlignment(Qt.AlignCenter)
            value.setStyleSheet("font-size: 24px; font-weight: bold;")
            status = QLabel("Offline")
            status.setAlignment(Qt.AlignCenter)
            box_layout.addWidget(value)
            box_layout.addWidget(status)
            self.card_values[sensor_id] = value
            self.card_status[sensor_id] = status
            cards.addWidget(box, index // 3, index % 3)
        layout.addLayout(cards)

        splitter = QSplitter(Qt.Vertical)
        self.sensor_table = QTableWidget(0, 6)
        self.sensor_table.setHorizontalHeaderLabels(["ID", "Sensor", "Wert", "Einheit", "Status", "Zeit"])
        self.sensor_table.horizontalHeader().setStretchLastSection(True)
        splitter.addWidget(self.sensor_table)

        self.trend_plot = pg.PlotWidget()
        self.trend_plot.setBackground("w")
        self.trend_plot.setTitle("Live-Trend Simulator / MCS-4")
        self.trend_plot.setLabel("left", "Wert")
        self.trend_plot.setLabel("bottom", "Samples")
        self.trend_plot.showGrid(x=True, y=True)
        self.trend_plot.addLegend()
        splitter.addWidget(self.trend_plot)
        splitter.setSizes([260, 380])
        layout.addWidget(splitter, 1)
        return tab

    def _create_telegram_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.telegram_log = QPlainTextEdit()
        self.telegram_log.setReadOnly(True)
        layout.addWidget(self.telegram_log)
        return tab

    def _create_alarm_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.alarm_log = QPlainTextEdit()
        self.alarm_log.setReadOnly(True)
        layout.addWidget(self.alarm_log)
        return tab

    def _create_diagnostics_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.diagnostics = QPlainTextEdit()
        self.diagnostics.setReadOnly(True)
        layout.addWidget(self.diagnostics)
        return tab

    def _refresh_ports(self) -> None:
        self.port_box.clear()
        ports = ComPortManager.list_ports()
        if not ports:
            self.port_box.addItem("Kein COM-Port gefunden", "")
            self.adapter_label.setText("Adapter: kein COM-Port")
            return
        preferred_index = 0
        for index, port in enumerate(ports):
            self.port_box.addItem(port.display_name, port.device)
            if port.is_likely_exsys:
                preferred_index = index
        self.port_box.setCurrentIndex(preferred_index)
        selected = ports[preferred_index]
        self.adapter_label.setText("Adapter: Exsys/USB-RS422 erkannt" if selected.is_likely_exsys else "Adapter: COM-Port erkannt")

    def start_acquisition(self) -> None:
        self.stop_acquisition()
        self.reader.reset()
        mode = self.mode_box.currentText()
        if mode == "Simulator":
            self.simulator = MCSSimulator()
            self.simulator.on_data = self._on_bytes_received
            self.simulator.on_log = self._log
            self.simulator.start()
            self.connection_started_at = datetime.now()
            self.status_label.setText("Status: Simulator läuft")
        else:
            port = self.port_box.currentData()
            if not port:
                self._log("Kein COM-Port ausgewählt.")
                self.status_label.setText("Status: kein COM-Port")
                return
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
                self.connection_started_at = datetime.now()
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
        self.connection_started_at = None

    def _on_bytes_received(self, data: bytes) -> None:
        self.byte_counter += len(data)
        packets = self.reader.feed(data)
        for raw in packets:
            self.telegram_log.appendPlainText(f"RX {raw.hex(' ').upper()}")
            try:
                packet = self.parser.parse(raw)
                decoded = self.decoder.decode(packet)
                sensor = self.sensors.update_from_decoded(decoded)
                self.history.insert_sensor(sensor)
                self.packet_counter += 1
                self._append_trend(sensor.sensor_id, sensor.value)
                for alarm in self.alarms.evaluate(sensor):
                    state = "AKTIV" if alarm.active else "INAKTIV"
                    self.alarm_log.appendPlainText(f"{alarm.timestamp:%H:%M:%S} [{state}] {alarm.text}")
                self._update_sensor_table()
                self._update_sensor_cards()
            except PacketParseError as exc:
                self.error_counter += 1
                self._log(f"Parserfehler: {exc}")

    def _append_trend(self, sensor_id: int, value: float) -> None:
        self.trend_history[sensor_id].append(value)
        if sensor_id not in self.trend_curves:
            name = self.sensors.get(sensor_id).name if self.sensors.get(sensor_id) else f"Sensor {sensor_id}"
            self.trend_curves[sensor_id] = self.trend_plot.plot([], [], name=name)
        y = list(self.trend_history[sensor_id])
        x = list(range(len(y)))
        self.trend_curves[sensor_id].setData(x, y)

    def _update_sensor_cards(self) -> None:
        for sensor in self.sensors.all_sensors():
            if sensor.sensor_id in self.card_values:
                self.card_values[sensor.sensor_id].setText(f"{sensor.value:.2f} {sensor.unit}")
                self.card_status[sensor.sensor_id].setText(sensor.status_text)
                if sensor.alarm:
                    self.card_status[sensor.sensor_id].setStyleSheet("color: red; font-weight: bold;")
                elif sensor.online:
                    self.card_status[sensor.sensor_id].setStyleSheet("color: green; font-weight: bold;")
                else:
                    self.card_status[sensor.sensor_id].setStyleSheet("color: gray;")

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
                if sensor.alarm:
                    item.setBackground(QColor(255, 220, 220))
                elif sensor.online:
                    item.setBackground(QColor(225, 255, 225))
                self.sensor_table.setItem(row, col, item)

    def _update_diagnostics(self) -> None:
        active_alarms = self.alarms.active_alarms()
        text = (
            f"Zeit: {datetime.now():%Y-%m-%d %H:%M:%S}\n"
            f"Empfangene Bytes: {self.byte_counter}\n"
            f"Empfangene Telegramme: {self.packet_counter}\n"
            f"Parserfehler: {self.error_counter}\n"
            f"Sensoren: {len(self.sensors.all_sensors())}\n"
            f"Aktive Alarme: {len(active_alarms)}\n"
            f"Laufzeit: {self._runtime_text()}\n"
            f"Modus: {self.mode_box.currentText()}\n"
        )
        self.diagnostics.setPlainText(text)

    def _log(self, message: str) -> None:
        self.telegram_log.appendPlainText(f"LOG {datetime.now():%H:%M:%S} {message}")

    def _runtime_text(self) -> str:
        if not self.connection_started_at:
            return "-"
        seconds = int((datetime.now() - self.connection_started_at).total_seconds())
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt API
        self.stop_acquisition()
        event.accept()
