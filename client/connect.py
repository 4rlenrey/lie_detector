import sys
import csv
import serial
import time
from datetime import datetime
from PySide6.QtCore import QThread, Signal, Slot, QObject
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton
import serial.tools.list_ports

from client.constants import SECONDS_RECORDING, SERIAL_COMMUNICATION_BITS

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
        # Connect to the Arduino
        with serial.Serial(self.serial_port, 115200, timeout=1) as ser:
            self.running = True
            start_time = time.time()
            while self.running and (time.time() - start_time < SECONDS_RECORDING):
                # Read a line from the Arduino
                line = ser.readline().decode('utf-8').rstrip()
                print(line)

                if line:
                    data = line.split(',')
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

    def stop_recording_and_save(self):
        self.reader.stop()
        self.reader.wait()  # Ensure the thread has finished

        # Save the recording to a CSV file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"data/recordings/{timestamp}_recording.csv"
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Timestamp', 'Red', 'IR', 'GSR'])
            writer.writerows(self.recording)
        print(f"Recording saved to {filename}")

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
        self.setWindowTitle('Arduino Data Recorder')
        self.show()



def read_from_arduino(serial_port):
    # Connect to the Arduino
    with serial.Serial(serial_port, 115200, timeout=1) as ser:
        while True:
            # Read a line from the Arduino
            line = ser.readline().decode('utf-8').rstrip()
            if line:
                print(line)


# if __name__ == "__main__":
#     arduino_port = find_arduino_port()
#     if arduino_port:
#         print(f"Arduino found on port {arduino_port}")
#         read_from_arduino(arduino_port)
#     else:
#         print("Arduino not found")
