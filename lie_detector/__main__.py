import sys

from PySide6.QtWidgets import QApplication

from lie_detector.connect import find_arduino_port
from lie_detector.constants import (ANSWERS_DIR, MODEL_PATH, PLOTS_DIR,
                                    RECORDINGS_DIR, RECORDINGS_PROCESSED_DIR)
from lie_detector.Window import MainWindowApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    serial_port = find_arduino_port()
    main_window = MainWindowApp(
        serial_port, RECORDINGS_DIR, RECORDINGS_PROCESSED_DIR, PLOTS_DIR, MODEL_PATH, ANSWERS_DIR
    )
    main_window.show()
    sys.exit(app.exec())
