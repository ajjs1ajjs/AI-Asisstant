# 🚀 AI Coding IDE - Ultra Compact Version
import sys
import os
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Завантаження стилів
    if os.path.exists("style.qss"):
        with open("style.qss", "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
            
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
