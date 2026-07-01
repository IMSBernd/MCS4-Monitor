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

from core.com_ports import list_com_ports
from core.simulator import MCSSimulator
from model.sensor_store import SensorStore
from protocol.decoder import BasicMCS4Decoder
from protocol.packet_reader import PacketReader


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MCS-4 Professional Monitor - Clean Base 0.6")
        self.resize(1200, 760)

        self.simulator: MCSSimulator | None = None
        self.reader = PacketReader()
        self.decoder = BasicMCS4Decoder()
        self.sensors = SensorStore()
        self.packet_count = 0
        self.error_count = 0

        self.sim_timer = QTimer(self)
        self.sim_timer.timeout.connect(self._simulator_tick)

        self.diag_timer = QTimer(self)
        self.diag_timer.timeout.connect(self._update_diagnostics)
        self.diag_timer.start(1000)

        self._build_ui()
        self._refresh_ports()
        self._update_diagnostics()

    def _build_ui(self) -> None:
        root = QWidget()
        main_layout = QVBoxLayout(root)

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
        main_layout.addLayout(top)

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

        main_layout.addWidget(tabs)
        self.setCentralWidget(root)

        self.refresh_button.clicked.connect(self._refresh_ports)
        self.start_button.clicked.connect(self.start)
        self.stop_button.clicked.connect(self.stop)

    def _refresh_ports(self) -> None:
        self.port_box.clear()
        ports = list_com_ports()
        if not ports:
            self.port_box.addItem("Kein COM-Port gefunden", "")
            return
        for port in ports:
            self.port_box.addItem(port.display_name, port.device)

    def start(self) -> None:
        self.stop()
        if self.mode_box.currentText() == "Simulator":
            self.simulator = MCSSimulator()
            self.sim_timer.start(250)
            self.status_label.setText("Status: Simulator läuft")
            self._log("Simulator gestartet")
            return

        self.status_label.setText("Status: RS422 noch nicht aktiviert")
        self._log("RS422 folgt im nächsten Schritt; bitte vorerst Simulator nutzen.")

    def stop(self) -> None:
        if self.sim_timer.isActive():
            self.sim_timer.stop()
        if self.simulator is not None:
            self.simulator = None
            self._log("Simulator gestoppt")
        self.status_label.setText("Status: gestoppt")

    def _simulator_tick(self) -> None:
        if self.simulator is None:
            return
        self._process_bytes(self.simulator.next_bytes())

    def _process_bytes(self, data: bytes) -> None:
        for raw in self.reader.feed(data):
            self.telegram_log.appendPlainText(f"RX {raw.hex(' ').upper()}")
            try:
                decoded = self.decoder.decode(raw)
                sensor = self.sensors.update(
                    decoded.sensor_id,
                    decoded.name,
                    decoded.value,
                    decoded.unit,
                    decoded.timestamp,
                )
                self.packet_count += 1
                if sensor.status == "ALARM":
                    self.alarm_log.appendPlainText(
                        f"{sensor.timestamp:%H:%M:%S} ALARM {sensor.name}: {sensor.value:.2f} {sensor.unit}"
                    )
                self._update_table()
            except Exception as exc:
                self.error_count += 1
                self._log(f"Parserfehler: {exc}")

    def _update_table(self) -> None:
        sensors = self.sensors.all()
        self.sensor_table.setRowCount(len(sensors))
        for row, sensor in enumerate(sensors):
            values = [
                str(sensor.sensor_id),
                sensor.name,
                f"{sensor.value:.2f}",
                sensor.unit,
                sensor.status,
                sensor.timestamp.strftime("%H:%M:%S"),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col in (0, 2):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.sensor_table.setItem(row, col, item)

    def _update_diagnostics(self) -> None:
        self.diagnostics.setPlainText(
            f"Zeit: {datetime.now():%Y-%m-%d %H:%M:%S}\n"
            f"Telegramme: {self.packet_count}\n"
            f"Parserfehler: {self.error_count}\n"
            f"Sensoren: {len(self.sensors.all())}\n"
            f"Simulator aktiv: {self.simulator is not None}\n"
        )

    def _log(self, message: str) -> None:
        self.telegram_log.appendPlainText(f"LOG {datetime.now():%H:%M:%S} {message}")

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt naming
        self.stop()
        event.accept()
