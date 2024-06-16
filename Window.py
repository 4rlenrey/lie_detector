import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QPushButton,
    QGridLayout,
    QDialog,
    QDialogButtonBox,
    QLabel,
)
from PyQt5.QtCore import (QTimer)

import pandas as pd
os.makedirs("answers", exist_ok=True)

start_time = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = os.path.join("answers", f"answers_{start_time}.csv")

def get_random_question(filenames="questions.csv""never_have.cvs""better_questions.csv"):
    df = pd.read_csv(filenames, delimiter=";")
    random_question = str(df.sample(n=1)['question'].values[0])
    return random_question

def save_answer(question, answer, Truth, filename=filename):
    df = pd.DataFrame([[question, answer, Truth]], columns=['question', 'answer', 'Truth'])
    try:
        df.to_csv(filename, mode='a', header=False, index=False)
    except FileNotFoundError:
        df.to_csv(filename, mode='w', header=True, index=False)

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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.current_question = None
        self.time_left = 10

        central_widget = QWidget()
        self.setWindowTitle("data collector") 
        
        layout = QGridLayout(central_widget)

        self.label = QLabel('Do you want to start')
        self.timer_label = QLabel('Time left: 10s')
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
    
        
    def record_answer(self, answer):
        if self.current_question:
            self.timer.stop()
            if answer != "No answer":
                dialog = TruthLieDialog(self.current_question, answer)
                Truth = dialog.get_truth_lie()
                save_answer(self.current_question, answer, "Truth" if Truth else "Lie")
            else:
                save_answer(self.current_question, answer,"")
        self.current_question = get_random_question('questions.csv')
        self.label.setText(self.current_question)
        self.time_left = 10 
        self.timer_label.setText(f'Time left: {self.time_left}s')
        self.timer.start(1000)
        
    def handle_timeout(self):
        self.time_left -= 1
        self.timer_label.setText(f'Time left: {self.time_left}s')
        if self.time_left == 0:
            self.timer.stop()
            self.record_answer("No answer")

def main():
    app = QApplication(sys.argv)
    mainwindow = MainWindow()
    mainwindow.show()
    sys.exit(app.exec_())
    

if __name__ =="__main__":
    main()
    