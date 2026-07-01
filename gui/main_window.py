import math
import random
import sys
from collections import defaultdict, deque
from datetime import datetime

import pyqtgraph as pg
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QApplication,
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

try:
    import serial
    from serial.tools import list_ports
except Exception:
    serial = None
    list_ports = None


def hex_string(data: bytes) -> str:
    return " ".join(f"{b:02X}" for b in data)


def make_packet(channel: int, unit_code: int, value: int) -> bytes:
    value = max(0, min(value, 0x3FFF))
    return bytes([
        0xFF,
        0x00,
        0x01,
        0x02,
        channel & 0xFF,
        unit_code & 0x0F,
        (value >> 8) & 0x3F,
        value & 0xFF,
    ])


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MCS-4 Monitor - Version 0.6 Sensor & Alarm")
        self.resize(1300, 820)

        self.t = 0.0
        self.packet_count = 0
        self.byte_count = 0
        self.serial_port = None
        self.buffer = bytearray()

        self.sensor_names = {
            1: "Öltemperatur",
            2: "Öldruck",
            3: "Drehzahl",
            4: "Kühlwasser",
            5: "Abgastemperatur",
        }

        self.units = {
            1: "°C",
            2: "bar",
            3: "rpm",
        }

        self.limits = {
            1: {"warn_low": 0, "warn_high": 90, "alarm_low": -10, "alarm_high": 95},
            2: {"warn_low": 4.5, "warn_high": 6.0, "alarm_low": 4.0, "alarm_high": 6.5},
            3: {"warn_low": 500, "warn_high": 1900, "alarm_low": 300, "alarm_high": 2100},
            4: {"warn_low": 0, "warn_high": 88, "alarm_low": -10, "alarm_high": 95},
            5: {"warn_low": 0, "warn_high": 520, "alarm_low": -10, "alarm_high": 560},
        }

        self.sensor_values = {}
        self.active_alarms = {}
        self.trend_data = defaultdict(lambda: deque(maxlen=200))
        self.curves = {}

        self._build_ui()
        self.refresh_ports()

        self.sim_timer = QTimer(self)
        self.sim_timer.timeout.connect(self.update_simulator)

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

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Sensor", "Wert", "Einheit", "Status", "Alarm", "Zeit"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.tabs.addTab(self.table, "Dashboard")

        self.trend_plot = pg.PlotWidget()
        self.trend_plot.setBackground("w")
        self.trend_plot.showGrid(x=True, y=True)
        self.trend_plot.addLegend()
        self.trend_plot.setLabel("left", "Wert")
        self.trend_plot.setLabel("bottom", "Zeitpunkte")
        self.tabs.addTab(self.trend_plot, "Trend")

        self.telegram_log = QPlainTextEdit()
        self.telegram_log.setReadOnly(True)
        self.tabs.addTab(self.telegram_log, "Telegramme")

        self.decoder_log = QPlainTextEdit()
        self.decoder_log.setReadOnly(True)
        self.tabs.addTab(self.decoder_log, "Decoder")

        self.alarm_log = QPlainTextEdit()
        self.alarm_log.setReadOnly(True)
        self.tabs.addTab(self.alarm_log, "Alarme")

        self.diagnostics = QPlainTextEdit()
        self.diagnostics.setReadOnly(True)
        self.tabs.addTab(self.diagnostics, "Diagnose")

        layout.addWidget(self.tabs)
        self.setCentralWidget(root)

        self.refresh_btn.clicked.connect(self.refresh_ports)
        self.start_btn.clicked.connect(self.start)
        self.stop_btn.clicked.connect(self.stop)

    def refresh_ports(self):
        self.port_box.clear()

        if list_ports is None:
            self.port_box.addItem("pyserial nicht verfügbar", "")
            return

        ports = list(list_ports.comports())

        if not ports:
            self.port_box.addItem("Kein COM-Port gefunden", "")
            return

        for port in ports:
            self.port_box.addItem(f"{port.device} - {port.description}", port.device)

    def start(self):
        self.stop()

        self.telegram_log.clear()
        self.decoder_log.clear()
        self.alarm_log.clear()
        self.buffer.clear()

        if self.mode.currentText() == "Simulator":
            self.status.setText("Status: Simulator läuft")
            self.log("Simulator gestartet")
            self.sim_timer.start(250)
            return

        self.start_rs422()

    def stop(self):
        self.sim_timer.stop()
        self.serial_timer.stop()

        if self.serial_port is not None:
            try:
                self.serial_port.close()
                self.log("RS422 geschlossen")
            except Exception as exc:
                self.log(f"Fehler beim Schließen: {exc}")
            self.serial_port = None

        self.status.setText("Status: gestoppt")

    def start_rs422(self):
        if serial is None:
            self.status.setText("Status: pyserial fehlt")
            self.log("pyserial ist nicht verfügbar")
            return

        port = self.port_box.currentData()

        if not port:
            self.status.setText("Status: Kein COM-Port")
            self.log("Kein COM-Port ausgewählt")
            return

        try:
            self.serial_port = serial.Serial(
                port=port,
                baudrate=38400,
                bytesize=8,
                parity=serial.PARITY_ODD,
                stopbits=1,
                timeout=0,
            )

            self.status.setText(f"Status: RS422 verbunden {port}")
            self.log(f"RS422 geöffnet: {port}, 38400 Baud, 8O1")
            self.serial_timer.start(50)

        except Exception as exc:
            self.status.setText("Status: RS422 Fehler")
            self.log(f"RS422 Fehler: {exc}")

    def read_serial(self):
        if self.serial_port is None:
            return

        try:
            waiting = self.serial_port.in_waiting

            if waiting <= 0:
                return

            data = self.serial_port.read(waiting)
            self.byte_count += len(data)

            if data:
                self.telegram_log.appendPlainText(
                    f"RX {datetime.now():%H:%M:%S.%f}  {hex_string(data)}"
                )
                self.process_bytes(data)

        except Exception as exc:
            self.log(f"Lesefehler RS422: {exc}")
            self.stop()

    def update_simulator(self):
        self.t += 0.25

        oil_temp = 82 + 3 * math.sin(self.t)
        oil_pressure = 5.2 + 0.2 * math.sin(self.t / 2)
        rpm = 1480 + 60 * math.sin(self.t / 3)
        coolant = 79 + 2.5 * math.cos(self.t)
        exhaust = 460 + random.randint(-8, 8)

        # absichtlich gelegentlich erhöhte Werte, damit Warn-/Alarmfunktion sichtbar wird
        if int(self.t) % 30 > 24:
            oil_temp += 14
        if int(self.t) % 40 > 34:
            exhaust += 120

        packets = bytearray()
        packets += make_packet(1, 1, int(oil_temp * 10))
        packets += make_packet(2, 2, int(oil_pressure * 100))
        packets += make_packet(3, 3, int(rpm))
        packets += make_packet(4, 1, int(coolant * 10))
        packets += make_packet(5, 1, int(exhaust * 10))

        self.byte_count += len(packets)

        self.telegram_log.appendPlainText(f"RX {hex_string(bytes(packets))}")
        self.process_bytes(bytes(packets))

    def process_bytes(self, data: bytes):
        self.buffer.extend(data)

        while True:
            if 0xFF not in self.buffer:
                self.buffer.clear()
                return

            sync_index = self.buffer.index(0xFF)

            if sync_index > 0:
                del self.buffer[:sync_index]

            if len(self.buffer) < 8:
                return

            packet = bytes(self.buffer[:8])
            del self.buffer[:8]

            self.decode_packet(packet)

    def decode_packet(self, packet: bytes):
        if len(packet) != 8 or packet[0] != 0xFF:
            return

        header = packet[1]
        destination = packet[2]
        source = packet[3]
        channel = packet[4]
        unit_code = packet[5] & 0x0F
        msb = packet[6] & 0x3F
        lsb = packet[7]

        raw_value = (msb << 8) | lsb
        unit = self.units.get(unit_code, "")

        if unit == "°C":
            value = raw_value / 10.0
        elif unit == "bar":
            value = raw_value / 100.0
        else:
            value = float(raw_value)

        name = self.sensor_names.get(channel, f"Sensor {channel}")
        now = datetime.now().strftime("%H:%M:%S")

        state, alarm_text = self.evaluate_sensor(channel, name, value, unit)

        self.sensor_values[channel] = {
            "id": channel,
            "name": name,
            "value": value,
            "unit": unit,
            "state": state,
            "alarm": alarm_text,
            "time": now,
        }

        self.packet_count += 1

        self.decoder_log.appendPlainText(
            f"{now}  CH={channel}  {name} = {value:.2f} {unit}  "
            f"STATUS={state} SRC={source} DST={destination} HEADER={header:02X}"
        )

        self.update_dashboard()
        self.update_trend(channel, value, name)

    def evaluate_sensor(self, channel: int, name: str, value: float, unit: str):
        limits = self.limits.get(channel)

        if not limits:
            return "OK", ""

        alarm_key = channel
        text = ""

        if value <= limits["alarm_low"] or value >= limits["alarm_high"]:
            state = "ALARM"
            text = f"{name}: {value:.2f} {unit} außerhalb Alarmgrenze"
        elif value <= limits["warn_low"] or value >= limits["warn_high"]:
            state = "WARNUNG"
            text = f"{name}: {value:.2f} {unit} außerhalb Warngrenze"
        else:
            state = "OK"

        if state in {"WARNUNG", "ALARM"}:
            old = self.active_alarms.get(alarm_key)
            if old != text:
                self.active_alarms[alarm_key] = text
                self.alarm_log.appendPlainText(f"{datetime.now():%H:%M:%S} [{state}] {text}")
        else:
            if alarm_key in self.active_alarms:
                self.alarm_log.appendPlainText(
                    f"{datetime.now():%H:%M:%S} [OK] {name}: Wert wieder normal"
                )
                del self.active_alarms[alarm_key]

        return state, text

    def update_dashboard(self):
        sensors = list(self.sensor_values.values())
        sensors.sort(key=lambda s: s["id"])

        self.table.setRowCount(len(sensors))

        for row, sensor in enumerate(sensors):
            values = [
                str(sensor["id"]),
                sensor["name"],
                f"{sensor['value']:.2f}",
                sensor["unit"],
                sensor["state"],
                sensor["alarm"],
                sensor["time"],
            ]

            for col, text in enumerate(values):
                item = QTableWidgetItem(text)

                if col in (0, 2):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

                if sensor["state"] == "ALARM":
                    item.setBackground(Qt.red)
                    item.setForeground(Qt.white)
                elif sensor["state"] == "WARNUNG":
                    item.setBackground(Qt.yellow)
                    item.setForeground(Qt.black)
                elif sensor["state"] == "OK":
                    item.setBackground(Qt.white)
                    item.setForeground(Qt.black)

                self.table.setItem(row, col, item)

    def update_trend(self, channel: int, value: float, name: str):
        self.trend_data[channel].append(value)

        if channel not in self.curves:
            pen = pg.mkPen(width=2)
            self.curves[channel] = self.trend_plot.plot(
                [],
                [],
                pen=pen,
                name=name,
            )

        y_values = list(self.trend_data[channel])
        x_values = list(range(len(y_values)))
        self.curves[channel].setData(x_values, y_values)

    def update_diagnostics(self):
        text = (
            f"Zeit: {datetime.now():%Y-%m-%d %H:%M:%S}\n"
            f"Modus: {self.mode.currentText()}\n"
            f"Telegramme dekodiert: {self.packet_count}\n"
            f"Bytes empfangen/erzeugt: {self.byte_count}\n"
            f"Aktueller COM-Port: {self.port_box.currentData()}\n"
            f"RS422 aktiv: {'Ja' if self.serial_port else 'Nein'}\n"
            f"Sensoren im Dashboard: {len(self.sensor_values)}\n"
            f"Aktive Alarme: {len(self.active_alarms)}\n"
        )

        self.diagnostics.setPlainText(text)

    def log(self, text):
        self.telegram_log.appendPlainText(f"LOG {datetime.now():%H:%M:%S} {text}")

    def closeEvent(self, event):
        self.stop()
        event.accept()


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()