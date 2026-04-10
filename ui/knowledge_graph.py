# 📊 Knowledge Graph Visualizer
# Real-time project structure mapping.

import os
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QPen, QColor, QFont

class KnowledgeGraphWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #0f1115; border: none;")
        self.nodes = {}  # {path: pos}
        self.edges = []  # [(path1, path2)]
        self.setMinimumHeight(400)
        
    def update_graph(self, root_dir):
        """Builds a basic graph of files and folder hierarchy"""
        self.nodes = {}
        self.edges = []
        
        # Simple hierarchical layout engine
        y = 50
        for root, dirs, files in os.walk(root_dir):
            if ".git" in root or "__pycache__" in root:
                continue
            
            parent_node = os.path.basename(root)
            if parent_node not in self.nodes:
                self.nodes[parent_node] = QPointF(100, y)
                y += 60
            
            for f in files:
                if f.endswith((".py", ".md", ".txt", ".js", ".html", ".css")):
                    file_node = f
                    self.nodes[file_node] = QPointF(300, y)
                    self.edges.append((parent_node, file_node))
                    y += 40
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw Edges
        pen = QPen(QColor("#2d3139"), 1)
        painter.setPen(pen)
        for start_id, end_id in self.edges:
            if start_id in self.nodes and end_id in self.nodes:
                painter.drawLine(self.nodes[start_id], self.nodes[end_id])
        
        # Draw Nodes
        font = QFont("Inter", 8)
        painter.setFont(font)
        for name, pos in self.nodes.items():
            # Node Circle
            painter.setBrush(QColor("#4ec9b0"))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(pos, 4, 4)
            
            # Label
            painter.setPen(QColor("#94a3b8"))
            painter.drawText(pos.x() + 10, pos.y() + 5, name)
