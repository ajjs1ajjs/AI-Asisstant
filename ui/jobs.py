# ⏳ AI Background Jobs Widget (v6.0)
# Track autonomous agents working in the background.

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QListWidget, QProgressBar
from PySide6.QtCore import Qt

class BackgroundJobsWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #0f1115; border: none;")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        header = QLabel("⏳ Autonomous Background Jobs")
        header.setStyleSheet("color: #4ec9b0; font-weight: bold; font-size: 14px;")
        layout.addWidget(header)

        self.job_list = QListWidget()
        self.job_list.setStyleSheet("""
            QListWidget { background: #1e1e1e; border: 1px solid #333; color: #ddd; border-radius: 8px; padding: 5px; }
        """)
        layout.addWidget(self.job_list)

        self.progress = QProgressBar()
        self.progress.setStyleSheet("""
            QProgressBar { background: #2d2d30; border-radius: 4px; height: 10px; color: transparent; }
            QProgressBar::chunk { background: #4ec9b0; border-radius: 4px; }
        """)
        self.progress.setValue(0)
        layout.addWidget(self.progress)

    def add_job(self, name):
        self.job_list.addItem(f"🕒 {name} - Running...")
        self.progress.setValue(30)

    def finish_job(self, name):
        # Update existing item instead of just adding a new one
        for i in range(self.job_list.count()):
            if name in self.job_list.item(i).text():
                self.job_list.item(i).setText(f"✅ {name} - Completed (Auto-Synced)")
        self.progress.setValue(100)
