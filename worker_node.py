"""
Worker Node - Slave mode for distributed inference
Run this on secondary PCs to share their GPU/model resources
"""

import socket
import os
import sys
import threading
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QMessageBox,
    QCheckBox,
)
from PySide6.QtCore import Signal, QThread


class WorkerServer(QThread):
    request_received = Signal(dict)
    status_changed = Signal(str)

    def __init__(self, port=8765, parent=None):
        super().__init__(parent)
        self.port = port
        self.running = False
        self.server = None

    def run(self):
        self.running = True
        self.status_changed.emit(f"🚀 Worker server started on port {self.port}")
        self.start_server()

    def start_server(self):
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                if self.path == "/inference":
                    content_length = int(self.headers.get("Content-Length", 0))
                    body = self.rfile.read(content_length)
                    import json

                    try:
                        data = json.loads(body)
                        from local_engine import get_inference

                        engine = get_inference()
                        if engine.is_loaded:
                            result = engine.chat(data.get("messages", []))
                            self.send_response(200)
                            self.send_header("Content-Type", "application/json")
                            self.end_headers()
                            self.wfile.write(
                                json.dumps(
                                    {
                                        "status": "success",
                                        "response": result,
                                        "node": socket.gethostname(),
                                    }
                                ).encode()
                            )
                        else:
                            self.send_response(503)
                            self.end_headers()
                            self.wfile.write(b'{"error": "Model not loaded"}')
                    except Exception as e:
                        self.send_response(500)
                        self.end_headers()
                        self.wfile.write(json.dumps({"error": str(e)}).encode())
                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, format, *args):
                pass  # Suppress logging

        self.server = HTTPServer(("0.0.0.0", self.port), Handler)
        self.server.serve_forever()

    def stop(self):
        self.running = False
        if self.server:
            self.server.shutdown()
        self.status_changed.emit("⏹️ Worker server stopped")


class AddWorkerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Додати Worker ПК")
        self.resize(400, 200)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("IP адреса або ім'я ПК:"))
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("192.168.1.100 або PC-NAME")
        layout.addWidget(self.host_input)

        layout.addWidget(QLabel("Порт (за замовчуванням 8765):"))
        self.port_input = QLineEdit("8765")
        layout.addWidget(self.port_input)

        self.auto_detect_btn = QPushButton("🔍 Пошук в мережі")
        self.auto_detect_btn.clicked.connect(self.auto_detect)
        layout.addWidget(self.auto_detect_btn)

        layout.addWidget(QLabel("Знайдені ПК:"))
        self.found_list = QTextEdit()
        self.found_list.setReadOnly(True)
        self.found_list.setMaximumHeight(80)
        layout.addWidget(self.found_list)

        btns = QHBoxLayout()
        self.ok_btn = QPushButton("Додати")
        self.ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Відміна")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(self.ok_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)

    def auto_detect(self):
        import socket

        self.found_list.append("Сканування мережі...")

        # Get local network range
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            # Assume /24 subnet
            base_ip = ".".join(local_ip.split(".")[:3])

            found = []
            for i in range(1, 255):
                ip = f"{base_ip}.{i}"
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(0.1)
                    result = sock.connect_ex((ip, 8765))
                    sock.close()
                    if result == 0:
                        found.append(ip)
                        self.found_list.append(f"✓ Знайдено: {ip}")
                except:
                    pass

            if not found:
                self.found_list.append(
                    "Worker ноди не знайдено. Переконайся що на іншому ПК увімкнено Worker Mode."
                )
        except Exception as e:
            self.found_list.append(f"Помилка: {e}")

    def get_worker_info(self):
        return self.host_input.text(), int(self.port_input.text())


class WorkerModeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Worker Node Mode")
        self.resize(400, 300)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("<h3>Режим Worker Node</h3>"))
        layout.addWidget(
            QLabel("Дозволити іншим ПК використовувати вашу модель для інференсу:")
        )

        self.enabled_check = QCheckBox("Увімкнути Worker Mode")
        self.enabled_check.setChecked(True)
        layout.addWidget(self.enabled_check)

        layout.addWidget(QLabel("Порт для підключень:"))
        self.port_input = QLineEdit("8765")
        layout.addWidget(self.port_input)

        self.status_label = QLabel("Статус: Неактивний")
        layout.addWidget(self.status_label)

        self.start_btn = QPushButton("▶️ Запустити Worker")
        self.start_btn.clicked.connect(self.toggle_worker)
        layout.addWidget(self.start_btn)

        self.info_label = QLabel("")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        layout.addWidget(
            QLabel(
                "<small>Інші ПК зможуть підключитись до вашого IP автоматично після запуску.</small>"
            )
        )

        btns = QHBoxLayout()
        close_btn = QPushButton("Закрити")
        close_btn.clicked.connect(self.close)
        btns.addWidget(close_btn)
        layout.addLayout(btns)

        self.worker_server = None

    def toggle_worker(self):
        if self.worker_server and self.worker_server.running:
            self.worker_server.stop()
            self.worker_server = None
            self.start_btn.setText("▶️ Запустити Worker")
            self.status_label.setText("Статус: Неактивний")
            self.info_label.setText("")
        else:
            port = int(self.port_input.text())
            self.worker_server = WorkerServer(port)
            self.worker_server.status_changed.connect(self.on_status_changed)
            self.worker_server.start()
            self.start_btn.setText("⏹️ Зупинити Worker")

    def on_status_changed(self, status):
        self.status_label.setText(f"Статус: {status}")
        if "started" in status:
            import socket

            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            self.info_label.setText(
                f"Інші ПК можуть підключитись до: {local_ip}:{self.port_input.text()}"
            )

    def closeEvent(self, event):
        if self.worker_server and self.worker_server.running:
            self.worker_server.stop()
        super().closeEvent(event)


def start_worker_server(port=8765):
    """Standalone worker server for running on secondary PC"""
    print(f"Starting Worker Node on port {port}...")
    print(f"Other PCs can connect to this machine's IP address")

    server = WorkerServer(port)
    server.start()

    # Keep running
    try:
        import time

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping worker server...")
        server.stop()


if __name__ == "__main__":
    # Can run standalone: python worker_node.py
    start_worker_server()
