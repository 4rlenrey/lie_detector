import os
from datetime import datetime

import pandas as pd
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QWidget,
)
from sklearn.model_selection import train_test_split

from lie_detector.connect import DataRecorder
from lie_detector.constants import QUESTIONS_PATH
from lie_detector.data_preprocessing.process_signals import process_signal
from lie_detector.predictor.predictor import LieDetectorModel


def get_random_question(filenames=QUESTIONS_PATH):
    df = pd.read_csv(filenames, delimiter=";")
    random_question = str(df.sample(n=1)["question"].values[0])
    return random_question


def save_answer(question, answer, Truth, filename):
    df = pd.DataFrame([[question, answer, Truth]], columns=["question", "answer", "Truth"])
    try:
        df.to_csv(filename, mode="a", header=False, index=False)
    except FileNotFoundError:
        df.to_csv(filename, mode="w", header=True, index=False)


class TruthLieDialog(QDialog):
    def __init__(self, question, answer, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Truth or a Lie")
        self.question = question
        self.answer = answer

        layout = QGridLayout(self)
        label = QLabel(f"Was your answer to '{self.question}' ('{self.answer}') the truth or a lie?")
        layout.addWidget(label)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Yes | QDialogButtonBox.No, self)
        self.buttonBox.button(QDialogButtonBox.Yes).setText("Truth")
        self.buttonBox.button(QDialogButtonBox.No).setText("Lie")
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        layout.addWidget(self.buttonBox)

    def get_truth_lie(self):
        return self.exec_() == QDialog.Accepted


class PredictionResultDialog(QDialog):
    def __init__(self, prediction, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Prediction Result")

        layout = QGridLayout(self)
        label = QLabel(f"The prediction is: {prediction}")
        layout.addWidget(label)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok, self)
        self.buttonBox.accepted.connect(self.accept)

        layout.addWidget(self.buttonBox)


class MainWindowApp(QMainWindow):
    def __init__(self, serial_port, recordings_dir, recordings_processed_dir, plots_dir, model_path, answers_dir):
        super().__init__()

        self.recordings_dir = recordings_dir
        self.recordings_processed_dir = recordings_processed_dir
        self.plots_dir = plots_dir
        self.serial_port = serial_port
        self.model_path = model_path
        self.answers_dir = answers_dir

        self.lie_detector = LieDetectorModel(self.recordings_processed_dir, self.answers_dir)

        if not os.path.exists(self.model_path):
            self.train_model()
        else:
            self.lie_detector.load_model(self.model_path)

        self.recorder = DataRecorder(self.serial_port)

        self.current_question = None
        self.time_left = 10

        central_widget = QWidget()
        self.setWindowTitle("Lie detector")

        layout = QGridLayout(central_widget)

        self.label = QLabel("Do you want to start")
        self.timer_label = QLabel("Time left: 10s")
        button1 = QPushButton("Yes")
        button2 = QPushButton("No")

        layout.addWidget(self.label, 0, 0)
        layout.addWidget(self.timer_label, 2, 0)
        layout.addWidget(button1, 1, 0)
        layout.addWidget(button2, 1, 1)

        button1.clicked.connect(lambda: self.record_answer("Yes"))
        button2.clicked.connect(lambda: self.record_answer("No"))

        self.setCentralWidget(central_widget)

        self.timer = QTimer()
        self.timer.timeout.connect(self.handle_timeout)

    def freeze_window(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QTimer.singleShot(2000, self.unfreeze_window)

    def unfreeze_window(self):
        QApplication.restoreOverrideCursor()

    def record_answer(self, answer):
        if self.current_question:
            self.timer.stop()
            self.setDisabled(True)
            QTimer.singleShot(self.time_left * 1000, lambda: self.finish_answer(answer))
        else:
            self.new_question()

    def new_question(self):
        self.current_question = get_random_question()
        self.label.setText(self.current_question)
        self.time_left = 10
        self.timer_label.setText(f"Time left: {self.time_left}s")

        self.start_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filename = os.path.join(self.answers_dir, f"answers_{self.start_time}.csv")

        self.timer.start(1000)
        self.recorder.start_recording()

    def finish_answer(self, answer):
        truth = False
        if answer != "No answer":
            raw_recording_path = os.path.join(self.recordings_dir, f"recording_{self.start_time}.csv")
            self.recorder.stop_recording_and_save(raw_recording_path)
            new_path = process_signal(
                data_path=raw_recording_path, output_dir=self.recordings_processed_dir, plot_dir=self.plots_dir
            )
            self.predict_lie(new_path)
            dialog = TruthLieDialog(self.current_question, answer)
            truth = dialog.get_truth_lie()
            save_answer(self.current_question, answer, "Truth" if truth else "Lie", filename=self.filename)
        else:
            save_answer(self.current_question, answer, "", filename=self.filename)

        self.setEnabled(True)
        self.new_question()

    def handle_timeout(self):
        self.time_left -= 1
        self.timer_label.setText(f"Time left: {self.time_left}s")
        if self.time_left == 0:
            self.timer.stop()
            self.record_answer("No answer")

    def train_model(self):
        data, labels = self.lie_detector.load_data()
        X, y = self.lie_detector.preprocess_data(data, labels)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=42)
        self.lie_detector.train_model(X_train, y_train, X_test, y_test, epochs=10, batch_size=32)
        self.lie_detector.save_model(self.model_path)

    def predict_lie(self, data_file):
        data_df = pd.read_csv(data_file)
        data = data_df.to_numpy()
        prediction = self.lie_detector.predict(data)
        print(prediction[0][0])
        lie_or_truth = "Lie" if prediction[0][0] < 0.5 else "Truth"
        self.show_prediction_result(lie_or_truth)

    def show_prediction_result(self, prediction):
        result_dialog = PredictionResultDialog(prediction, self)
        result_dialog.exec_()
