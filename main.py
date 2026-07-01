import math
import random
import sys
from datetime import datetime

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication, QComboBox, QHBoxLayout, QLabel, QMainWindow,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MCS-4 Monitor - Clean Test")
        self.resize(1000, 600)

        self.t = 0.0

        root = QWidget()
        layout = QVBoxLayout(root)

        top = QHBoxLayout()
        self.mode = QComboBox()
        self.mode.addItems(["Simulator", "RS422"])
        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")
        self.status = QLabel("Status: bereit")

        top.addWidget(QLabel("Modus:"))
        top.addWidget(self.mode)
        top.addWidget(self.start_btn)
        top.addWidget(self.stop_btn)
        top.addStretch()
        top.addWidget(self.status)

        layout.addLayout(top)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Sensor", "Wert", "Einheit", "Zeit"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        self.setCentralWidget(root)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_simulator)

        self.start_btn.clicked.connect(self.start)
        self.stop_btn.clicked.connect(self.stop)

    def start(self):
        self.status.setText("Status: Simulator läuft")
        self.timer.start(250)

    def stop(self):
        self.timer.stop()
        self.status.setText("Status: gestoppt")

    def update_simulator(self):
        self.t += 0.25

        sensors = [
            (1, "Öltemperatur", 82 + 3 * math.sin(self.t), "°C"),
            (2, "Öldruck", 5.2 + 0.2 * math.sin(self.t / 2), "bar"),
            (3, "Drehzahl", 1480 + 60 * math.sin(self.t / 3), "rpm"),
            (4, "Kühlwasser", 79 + 2.5 * math.cos(self.t), "°C"),
            (5, "Abgastemperatur", 460 + random.randint(-8, 8), "°C"),
        ]

        self.table.setRowCount(len(sensors))

        now = datetime.now().strftime("%H:%M:%S")

        for row, (sid, name, value, unit) in enumerate(sensors):
            values = [
                str(sid),
                name,
                f"{value:.2f}",
                unit,
                now,
            ]

            for col, text in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(text))


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()