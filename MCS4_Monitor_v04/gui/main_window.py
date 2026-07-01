from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path

import pyqtgraph as pg
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
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
from core.com_port_manager import ComPortInfo, ComPortManager
from core.config import AppConfig
from core.sensor_manager import SensorManager
from core.serial_driver import SerialDriver
from core.simulator import MCSSimulator
from core.telegram_recorder import TelegramRecorder
from database.history import HistoryDatabase
from protocol.mcs4_decoder import MCS4Decoder
from protocol.packet_reader import PacketReader
from protocol.parser import PacketParseError, PacketParser


class MainWindow(QMainWindow):
    """Hauptfenster der MCS-4 Diagnose-Software.

    Version 0.4 ergänzt die erste echte Kommunikationsansicht: COM-Port-Details,
    HEX-Telegrammmonitor, Recorder und Diagnosezähler. Simulator und RS422 bleiben
    gleichwertige Datenquellen, damit die Software ohne Hardware weiterentwickelt
    werden kann.
    """

    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        self.setWindowTitle(f"{config.app_name} - Version 0.4")
        self.resize(1320, 860)

        self.reader = PacketReader(config.packet.sync_byte, config.packet.length)
        self.parser = PacketParser(config.packet.sync_byte, config.packet.length)
        self.decoder = MCS4Decoder()
        self.sensors = SensorManager()
        self.alarms = AlarmManager()
        self.history = HistoryDatabase(config.database.path)
        self.recorder = TelegramRecorder()
        self.simulator: MCSSimulator | None = None
        self.serial_driver: SerialDriver | None = None
        self.available_ports: list[ComPortInfo] = []

        self.packet_counter = 0
        self.error_counter = 0
        self.byte_counter = 0
        self.raw_line_counter = 0
        self.connection_state = "bereit"
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
        self.status_label.setMinimumWidth(190)
        self.adapter_label.setMinimumWidth(260)
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
        self.tabs.addTab(self._create_settings_tab(), "Einstellungen")
        layout.addWidget(self.tabs)
        self.setCentralWidget(root)

        self.refresh_button.clicked.connect(self._refresh_ports)
        self.start_button.clicked.connect(self.start_acquisition)
        self.stop_button.clicked.connect(self.stop_acquisition)
        self.port_box.currentIndexChanged.connect(self._update_selected_port_details)

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

        toolbar = QHBoxLayout()
        self.pause_telegram_check = QCheckBox("Anzeige pausieren")
        self.auto_scroll_check = QCheckBox("Auto-Scroll")
        self.auto_scroll_check.setChecked(True)
        self.record_button = QPushButton("Aufzeichnung starten")
        self.clear_telegram_button = QPushButton("Telegramme löschen")
        toolbar.addWidget(self.pause_telegram_check)
        toolbar.addWidget(self.auto_scroll_check)
        toolbar.addStretch(1)
        toolbar.addWidget(self.record_button)
        toolbar.addWidget(self.clear_telegram_button)
        layout.addLayout(toolbar)

        self.telegram_log = QPlainTextEdit()
        self.telegram_log.setReadOnly(True)
        self.telegram_log.setMaximumBlockCount(5000)
        layout.addWidget(self.telegram_log)

        self.record_button.clicked.connect(self._toggle_recording)
        self.clear_telegram_button.clicked.connect(self.telegram_log.clear)
        return tab

    def _create_alarm_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.alarm_log = QPlainTextEdit()
        self.alarm_log.setReadOnly(True)
        self.alarm_log.setMaximumBlockCount(2000)
        layout.addWidget(self.alarm_log)
        return tab

    def _create_diagnostics_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.diagnostics = QPlainTextEdit()
        self.diagnostics.setReadOnly(True)
        layout.addWidget(self.diagnostics)
        return tab

    def _create_settings_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.port_details = QPlainTextEdit()
        self.port_details.setReadOnly(True)
        layout.addWidget(QLabel("COM-Port Details"))
        layout.addWidget(self.port_details)
        layout.addStretch(1)
        return tab

    def _refresh_ports(self) -> None:
        self.port_box.clear()
        self.available_ports = ComPortManager.list_ports()
        if not self.available_ports:
            self.port_box.addItem("Kein COM-Port gefunden", "")
            self.adapter_label.setText("Adapter: kein COM-Port")
            self.port_details.setPlainText("Kein COM-Port gefunden.\n\nHinweis: Der Exsys USB-RS422 Adapter muss eingesteckt sein und im Windows-Gerätemanager als COM-Port erscheinen.")
            return
        preferred_index = 0
        for index, port in enumerate(self.available_ports):
            self.port_box.addItem(port.display_name, port.device)
            if port.is_likely_exsys:
                preferred_index = index
        self.port_box.setCurrentIndex(preferred_index)
        self._update_selected_port_details()

    def _update_selected_port_details(self) -> None:
        index = self.port_box.currentIndex()
        if index < 0 or index >= len(self.available_ports):
            return
        port = self.available_ports[index]
        self.adapter_label.setText("Adapter: Exsys/USB-RS422 erkannt" if port.is_likely_exsys else "Adapter: COM-Port erkannt")
        self.port_details.setPlainText(
            f"Gerät: {port.device}\n"
            f"Beschreibung: {port.description}\n"
            f"Hersteller: {port.manufacturer}\n"
            f"Hardware-ID: {port.hwid}\n"
            f"Wahrscheinlich Exsys/USB-RS422: {'Ja' if port.is_likely_exsys else 'Nein'}\n\n"
            "Schnittstellenparameter für MCS-4:\n"
            f"Baudrate: {self.config.serial.baudrate}\n"
            f"Datenbits: {self.config.serial.bytesize}\n"
            f"Parität: {self.config.serial.parity}\n"
            f"Stopbits: {self.config.serial.stopbits}\n"
        )

    def start_acquisition(self) -> None:
        self.stop_acquisition()
        self.reader.reset()
        self.packet_counter = 0
        self.error_counter = 0
        self.byte_counter = 0
        self.raw_line_counter = 0
        mode = self.mode_box.currentText()
        if mode == "Simulator":
            self.simulator = MCSSimulator()
            self.simulator.on_data = self._on_bytes_received
            self.simulator.on_log = self._log
            self.simulator.start()
            self.connection_started_at = datetime.now()
            self.connection_state = "Simulator läuft"
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
                self.serial_driver.on_status = self._on_serial_status
                self.serial_driver.connect()
                self.connection_started_at = datetime.now()
                self.connection_state = f"verbunden mit {port}"
                self.status_label.setText(f"Status: verbunden mit {port}")
            except Exception as exc:
                self.connection_state = "Fehler"
                self.status_label.setText("Status: Fehler")
                self._log(f"Verbindungsfehler: {exc}")

    def stop_acquisition(self) -> None:
        if self.simulator:
            self.simulator.stop()
            self.simulator = None
        if self.serial_driver:
            self.serial_driver.disconnect()
            self.serial_driver = None
        self.connection_state = "gestoppt"
        self.status_label.setText("Status: gestoppt")
        self.connection_started_at = None

    def _on_serial_status(self, status: str) -> None:
        self.connection_state = status

    def _on_bytes_received(self, data: bytes) -> None:
        self.byte_counter += len(data)
        self.recorder.record_rx(data)
        self._append_raw_bytes(data)
        packets = self.reader.feed(data)
        for raw in packets:
            self._append_telegram(f"PKT {raw.data.hex(' ').upper()}")
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

    def _append_raw_bytes(self, data: bytes) -> None:
        self.raw_line_counter += 1
        self._append_telegram(f"RX  {datetime.now():%H:%M:%S.%f}  {data.hex(' ').upper()}")

    def _append_telegram(self, text: str) -> None:
        if self.pause_telegram_check.isChecked():
            return
        self.telegram_log.appendPlainText(text)
        if self.auto_scroll_check.isChecked():
            self.telegram_log.verticalScrollBar().setValue(self.telegram_log.verticalScrollBar().maximum())

    def _toggle_recording(self) -> None:
        if self.recorder.enabled:
            self.recorder.stop()
            self.record_button.setText("Aufzeichnung starten")
            self._log("Telegramm-Aufzeichnung gestoppt")
            return
        default_path = Path("logs") / f"telegram_record_{datetime.now():%Y%m%d_%H%M%S}.log"
        path, _ = QFileDialog.getSaveFileName(self, "Telegramm-Aufzeichnung speichern", str(default_path), "Log-Dateien (*.log);;Text-Dateien (*.txt);;Alle Dateien (*)")
        if not path:
            return
        self.recorder.start(path)
        self.record_button.setText("Aufzeichnung stoppen")
        self._log(f"Telegramm-Aufzeichnung gestartet: {path}")

    def _append_trend(self, sensor_id: int, value: float) -> None:
        self.trend_history[sensor_id].append(value)
        if sensor_id not in self.trend_curves:
            sensor = self.sensors.get(sensor_id)
            name = sensor.name if sensor else f"Sensor {sensor_id}"
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
        telegram_rate = 0.0
        if self.connection_started_at:
            seconds = max(1.0, (datetime.now() - self.connection_started_at).total_seconds())
            telegram_rate = self.packet_counter / seconds
        text = (
            f"Zeit: {datetime.now():%Y-%m-%d %H:%M:%S}\n"
            f"Status: {self.connection_state}\n"
            f"Modus: {self.mode_box.currentText()}\n"
            f"Empfangene Bytes: {self.byte_counter}\n"
            f"Empfangene Rohzeilen: {self.raw_line_counter}\n"
            f"Empfangene Telegramme: {self.packet_counter}\n"
            f"Telegramme/s: {telegram_rate:.2f}\n"
            f"Parserfehler: {self.error_counter}\n"
            f"Sensoren: {len(self.sensors.all_sensors())}\n"
            f"Aktive Alarme: {len(active_alarms)}\n"
            f"Recorder aktiv: {'Ja' if self.recorder.enabled else 'Nein'}\n"
            f"Recorder-Datei: {self.recorder.path if self.recorder.path else '-'}\n"
            f"Laufzeit: {self._runtime_text()}\n"
        )
        self.diagnostics.setPlainText(text)

    def _log(self, message: str) -> None:
        self._append_telegram(f"LOG {datetime.now():%H:%M:%S} {message}")

    def _runtime_text(self) -> str:
        if not self.connection_started_at:
            return "-"
        seconds = int((datetime.now() - self.connection_started_at).total_seconds())
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt API
        self.recorder.stop()
        self.stop_acquisition()
        event.accept()
