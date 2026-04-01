# 🚀 AI Coding IDE - Ultra Compact Version
import sys
import os
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

def get_resource_path(filename):
    """Отримує шлях до ресурсу для PyInstaller"""
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

def main():
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Завантаження стилів
    style_path = get_resource_path("style.qss")
    if os.path.exists(style_path):
        with open(style_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
            
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
