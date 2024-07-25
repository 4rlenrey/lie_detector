import csv
import time

import serial
import serial.tools.list_ports
from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import QPushButton, QVBoxLayout, QWidget

from lie_detector.constants import SECONDS_RECORDING


def find_arduino_port():
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        if "Arduino" in port.description or "ttyUSB" in port.device or "ttyACM" in port.device:
            return port.device
    return None


class ArduinoReader(QThread):
    data_ready = Signal(list)

    def __init__(self, serial_port):
        super().__init__()
        self.serial_port = serial_port
        self.running = False

    def run(self):
        with serial.Serial(self.serial_port, 230400, timeout=1) as ser:
            self.running = True
            start_time = time.time()
            while self.running and (time.time() - start_time < SECONDS_RECORDING):
                line = ser.readline().decode("utf-8").rstrip()
                print(line)

                if line:
                    data = line.split(",")
                    if len(data) == 4:
                        timestamp, red, ir, gsr = data
                        self.data_ready.emit([timestamp, red, ir, gsr])
            self.running = False

    def stop(self):
        self.running = False


class DataRecorder(QObject):
    def __init__(self, serial_port):
        super().__init__()
        self.reader = ArduinoReader(serial_port)
        self.reader.data_ready.connect(self.record_data)
        self.recording = []

    @Slot(list)
    def record_data(self, data):
        self.recording.append(data)

    def start_recording(self):
        self.recording = []
        self.reader.start()

    def stop_recording_and_save(self, path):
        self.reader.stop()
        self.reader.wait()

        with open(path, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(self.recording)
        print(f"Recording saved to {path}")
        self.recording = []


class MainWindow(QWidget):
    def __init__(self, serial_port):
        super().__init__()
        self.recorder = DataRecorder(serial_port)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.start_button = QPushButton("Start Recording")
        self.start_button.clicked.connect(self.recorder.start_recording)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop and Save Recording")
        self.stop_button.clicked.connect(self.recorder.stop_recording_and_save)
        layout.addWidget(self.stop_button)

        self.setLayout(layout)
        self.setWindowTitle("Arduino Data Recorder")
        self.show()
