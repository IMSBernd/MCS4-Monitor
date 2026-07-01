from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from core.config import load_config
from gui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    config = load_config("config.json")
    window = MainWindow(config)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
