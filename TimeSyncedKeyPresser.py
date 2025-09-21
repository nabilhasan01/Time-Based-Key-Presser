import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QTimeEdit, QSpinBox, QCheckBox, QLineEdit, QPushButton, QVBoxLayout, QTextEdit, QMessageBox
from PyQt5.QtCore import QTime, QThread, pyqtSignal
from PyQt5.QtGui import QIcon
import pydirectinput
import time
from datetime import datetime, timedelta
import ntplib
import os

class KeyPressWorker(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, initial_time, loop_count, is_infinite, delay_seconds, key_to_press):
        super().__init__()
        self.initial_time = initial_time
        self.loop_count = loop_count
        self.is_infinite = is_infinite
        self.delay_seconds = delay_seconds
        self.key_to_press = key_to_press
        self._stop = False
        self.sync_clock()

    def sync_clock(self):
        try:
            client = ntplib.NTPClient()
            response = client.request('pool.ntp.org')
            offset = response.offset
            self.log_signal.emit(f"System clock synchronized with NTP server. Offset: {offset:.3f} seconds")
        except Exception as e:
            self.log_signal.emit(f"Failed to synchronize clock: {str(e)}")

    def run(self):
        now = datetime.now()
        target_time = now.replace(hour=self.initial_time.hour(), minute=self.initial_time.minute(), second=self.initial_time.second(), microsecond=0)

        if target_time < now:
            target_time += timedelta(days=1)

        if self.is_infinite:
            i = 0
            while not self._stop:
                self.wait_and_press(target_time, i)
                target_time += timedelta(seconds=self.delay_seconds)
                i += 1
        else:
            for i in range(self.loop_count):
                if self._stop:
                    break
                self.wait_and_press(target_time, i)
                target_time += timedelta(seconds=self.delay_seconds)

        self.finished_signal.emit()

    def wait_and_press(self, target_time, iteration):
        self.log_signal.emit(f"Iteration {iteration + 1}: Waiting until {target_time.strftime('%H:%M:%S')} to press '{self.key_to_press}'...")
        
        current_time = datetime.now()
        sleep_seconds = (target_time - current_time).total_seconds()
        while sleep_seconds > 0 and not self._stop:
            sleep_interval = min(0.1, sleep_seconds)
            time.sleep(sleep_interval)
            current_time = datetime.now()
            sleep_seconds = (target_time - current_time).total_seconds()

        if not self._stop:
            try:
                pydirectinput.press(self.key_to_press)
                self.log_signal.emit(f"'{self.key_to_press}' pressed at {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
            except Exception as e:
                self.log_signal.emit(f"Error pressing key: {str(e)}")

    def stop(self):
        self._stop = True

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        def resource_path(relative_path):
            """Get absolute path to resource, works for dev and for PyInstaller"""
            if hasattr(sys, '_MEIPASS'):
                # PyInstaller stores bundled files in sys._MEIPASS
                base_path = sys._MEIPASS
            else:
                base_path = os.path.abspath(".")
            return os.path.join(base_path, relative_path)

        icon_path = resource_path(os.path.join("resource", "icon.ico"))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.setWindowTitle("Time Based Key Clicker")
        self.setFixedSize(300, 550)
        self.layout = QVBoxLayout()
        

        # Initial Time
        self.time_label = QLabel("Initial Time (HH:MM:SS):")
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm:ss")  # Explicitly include seconds
        current_time = QTime.currentTime().addSecs(60)  # Set default to current time + 1 minute
        self.time_edit.setTime(QTime(current_time.hour(), current_time.minute(), 0))  # Set seconds to 00
        self.layout.addWidget(self.time_label)
        self.layout.addWidget(self.time_edit)

        # Loop Count
        self.loop_label = QLabel("Loop Count:")
        self.loop_spin = QSpinBox()
        self.loop_spin.setMinimum(1)
        self.loop_spin.setValue(10)
        self.layout.addWidget(self.loop_label)
        self.layout.addWidget(self.loop_spin)

        # Infinite Loop
        self.infinite_check = QCheckBox("Infinite Loop")
        self.infinite_check.stateChanged.connect(self.toggle_loop_spin)
        self.layout.addWidget(self.infinite_check)

        # Delay Seconds
        self.delay_label = QLabel("Delay between iterations (seconds):")
        self.delay_spin = QSpinBox()
        self.delay_spin.setMinimum(1)
        self.delay_spin.setValue(60)
        self.layout.addWidget(self.delay_label)
        self.layout.addWidget(self.delay_spin)

        # Key to Press
        self.key_label = QLabel("Key to Press (single character):")
        self.key_edit = QLineEdit()
        self.key_edit.setMaxLength(1)
        self.key_edit.setText("f")
        self.layout.addWidget(self.key_label)
        self.layout.addWidget(self.key_edit)

        # Log Area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.layout.addWidget(self.log_text)

        # Start Button
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_pressing)
        self.layout.addWidget(self.start_button)

        # Stop Button
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_pressing)
        self.stop_button.setEnabled(False)
        self.layout.addWidget(self.stop_button)

        self.setLayout(self.layout)
        self.worker = None

    def toggle_loop_spin(self):
        self.loop_spin.setEnabled(not self.infinite_check.isChecked())

    def start_pressing(self):
        key = self.key_edit.text().strip()
        if not key:
            QMessageBox.warning(self, "Error", "Please enter a key to press.")
            return
        if len(key) != 1 or not key.isalnum():
            QMessageBox.warning(self, "Error", "Key must be a single alphanumeric character.")
            return

        initial_time = self.time_edit.time()
        now = datetime.now()
        target_time = now.replace(hour=initial_time.hour(), minute=initial_time.minute(), second=initial_time.second(), microsecond=0)

        # Check if initial time has already passed
        if target_time <= now:
            QMessageBox.warning(self, "Error", "The selected initial time has already passed. Please choose a future time.")
            return

        loop_count = self.loop_spin.value()
        is_infinite = self.infinite_check.isChecked()
        delay_seconds = self.delay_spin.value()

        self.worker = KeyPressWorker(initial_time, loop_count, is_infinite, delay_seconds, key)
        self.worker.log_signal.connect(self.log_message)
        self.worker.finished_signal.connect(self.task_finished)
        self.worker.start()

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_pressing(self):
        if self.worker:
            self.worker.stop()
            self.log_message("Stopping...")
            self.worker.finished_signal.connect(self.task_finished)

    def log_message(self, message):
        self.log_text.append(message)

    def task_finished(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.log_message("Task stopped successfully.")

if __name__ == "__main__":
    pydirectinput.FAILSAFE = True
    app = QApplication(sys.argv)
    
    # Apply dark mode stylesheet
    app.setStyleSheet("""
        QWidget {
            background-color: #2E2E2E;
            color: #E0E0E0;
            font-size: 14px;
        }
        QLabel {
            color: #E0E0E0;
        }
        QTimeEdit, QSpinBox, QLineEdit {
            background-color: #3C3C3C;
            color: #E0E0E0;
            border: 1px solid #555555;
            padding: 5px;
        }
        QCheckBox {
            color: #E0E0E0;
        }
        QPushButton {
            background-color: #555555;
            color: #E0E0E0;
            border: 1px solid #555555;
            padding: 5px;
        }
        QPushButton:hover {
            background-color: #666666;
        }
        QPushButton:disabled {
            background-color: #444444;
            color: #888888;
        }
        QTextEdit {
            background-color: #3C3C3C;
            color: #E0E0E0;
            border: 1px solid #555555;
        }
    """)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())