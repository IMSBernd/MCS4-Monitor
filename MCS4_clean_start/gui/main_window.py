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

from core.ports import list_serial_ports
from core.simulator import EngineSimulator
from model.sensor import SensorValue


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MCS-4 Monitor - Clean Start 0.1")
        self.resize(1200, 760)

        self.simulator = EngineSimulator()
        self.running = False
        self.tick_count = 0
        self.sensor_map: dict[int, SensorValue] = {}

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._simulator_tick)

        self.diagnostic_timer = QTimer(self)
        self.diagnostic_timer.timeout.connect(self._update_diagnostics)
        self.diagnostic_timer.start(1000)

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

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "Sensor", "Wert", "Einheit", "Status", "Zeit"])
        self.table.horizontalHeader().setStretchLastSection(True)
        tabs.addTab(self.table, "Dashboard")

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
        self.start_button.clicked.connect(self.start_acquisition)
        self.stop_button.clicked.connect(self.stop_acquisition)

    def _refresh_ports(self) -> None:
        self.port_box.clear()
        ports = list_serial_ports()
        if not ports:
            self.port_box.addItem("Kein COM-Port gefunden", "")
            return
        for port, desc in ports:
            self.port_box.addItem(f"{port} - {desc}", port)

    def start_acquisition(self) -> None:
        mode = self.mode_box.currentText()
        if mode != "Simulator":
            self.status_label.setText("Status: RS422 kommt im nächsten Schritt")
            self._log("RS422-Modus ist vorbereitet, aber in dieser Clean-Start-Version noch deaktiviert.")
            return

        self.running = True
        self.timer.start(250)
        self.status_label.setText("Status: Simulator läuft")
        self._log("Simulator gestartet")

    def stop_acquisition(self) -> None:
        self.running = False
        self.timer.stop()
        self.status_label.setText("Status: gestoppt")
        self._log("Erfassung gestoppt")

    def _simulator_tick(self) -> None:
        values = self.simulator.next_values()
        self.tick_count += 1
        for value in values:
            self.sensor_map[value.sensor_id] = value
            if value.status != "OK":
                self.alarm_log.appendPlainText(
                    f"{value.timestamp:%H:%M:%S} ALARM {value.name}: {value.value} {value.unit}"
                )
        self._update_table()
        self.telegram_log.appendPlainText(
            f"SIM {datetime.now():%H:%M:%S.%f} Werte: "
            + ", ".join(f"{v.name}={v.value}{v.unit}" for v in values)
        )

    def _update_table(self) -> None:
        values = sorted(self.sensor_map.values(), key=lambda item: item.sensor_id)
        self.table.setRowCount(len(values))
        for row, sensor in enumerate(values):
            row_values = [
                str(sensor.sensor_id),
                sensor.name,
                f"{sensor.value:.2f}" if isinstance(sensor.value, float) else str(sensor.value),
                sensor.unit,
                sensor.status,
                sensor.timestamp.strftime("%H:%M:%S"),
            ]
            for col, text in enumerate(row_values):
                item = QTableWidgetItem(text)
                if col in (0, 2):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(row, col, item)

    def _update_diagnostics(self) -> None:
        self.diagnostics.setPlainText(
            f"Zeit: {datetime.now():%Y-%m-%d %H:%M:%S}\n"
            f"Status: {'läuft' if self.running else 'gestoppt'}\n"
            f"Simulator-Ticks: {self.tick_count}\n"
            f"Sensoren: {len(self.sensor_map)}\n"
            f"COM-Ports: {self.port_box.count()}\n"
        )

    def _log(self, message: str) -> None:
        self.telegram_log.appendPlainText(f"LOG {datetime.now():%H:%M:%S} {message}")

    def closeEvent(self, event) -> None:
        self.stop_acquisition()
        event.accept()
