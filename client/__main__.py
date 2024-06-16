import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton

from client.connect import MainWindow, find_arduino_port


if __name__ == '__main__':
    app = QApplication(sys.argv)
    serial_port = find_arduino_port()  # Replace with your actual serial port
    main_window = MainWindow(serial_port)
    sys.exit(app.exec())
