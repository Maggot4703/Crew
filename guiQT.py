import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QTreeWidget, QTreeWidgetItem, QMenu, QLineEdit, QComboBox, QTextEdit, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import logging
import threading

class TTSManager:
    def __init__(self, engine):
        self.engine = engine
        self.stop_event = threading.Event()

    def play_text(self, text, chunk_size=400):
        """Play text in chunks with stop event handling."""
        self.stop_event.clear()
        chunks = self._chunk_text(text, chunk_size)

        for chunk in chunks:
            if self.stop_event.is_set():
                break
            self.engine.say(chunk)
            self.engine.runAndWait()

    def stop(self):
        """Stop playback and clear the queue."""
        self.stop_event.set()
        self.engine.stop()

    def _chunk_text(self, text, max_length):
        """Split text into smaller chunks."""
        words = text.split()
        chunks = []
        current_chunk = []

        for word in words:
            current_chunk.append(word)
            if len(" ".join(current_chunk)) > max_length:
                chunks.append(" ".join(current_chunk))
                current_chunk = []

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

class CrewGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Crew GUI with PyQt5")
        self.setGeometry(100, 100, 1200, 800)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        self.status_label = QLabel("Status: Ready")
        self.layout.addWidget(self.status_label)

        self.data_table = QTreeWidget()
        self.data_table.setHeaderLabels(["Column 1", "Column 2", "Column 3"])
        self.layout.addWidget(self.data_table)

        self.details_text = QTextEdit()
        self.layout.addWidget(self.details_text)

        self.filter_input = QLineEdit()
        self.layout.addWidget(self.filter_input)

        self.filter_button = QPushButton("Apply Filter")
        self.filter_button.clicked.connect(self.apply_filter)
        self.layout.addWidget(self.filter_button)

        self.stop_button = QPushButton("Stop Reading")
        self.stop_button.clicked.connect(self.stop_reading)
        self.layout.addWidget(self.stop_button)

        self.tts_manager = TTSManager(None)  # Replace None with actual TTS engine

    def apply_filter(self):
        filter_text = self.filter_input.text()
        QMessageBox.information(self, "Filter Applied", f"Filter applied: {filter_text}")

    def stop_reading(self):
        try:
            self.tts_manager.stop()
            self.status_label.setText("Status: Reading stopped")
        except Exception as e:
            logging.error(f"Error stopping TTS: {e}")
            QMessageBox.critical(self, "Error", f"Failed to stop reading: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = CrewGUI()
    gui.show()
    sys.exit(app.exec_())