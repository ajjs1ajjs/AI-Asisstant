"""
Git Dialog для AI IDE
Інтерфейс для Git операцій
"""

from datetime import datetime
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

from git_integration import GitIntegration, GitStatus


class GitDialog(QDialog):
    """Діалог Git операцій"""

    commit_made = Signal(str)  # Сигнал про новий коміт

    def __init__(self, repo_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔀 Git")
        self.setModal(False)
        self.setMinimumSize(800, 600)
        self.resize(900, 700)
        
        self.git = GitIntegration(repo_path)
        self.setup_ui()
        self.refresh_status()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QFrame {
                background-color: #2d2d30;
                border-bottom: 1px solid #3e3e3e;
            }
        """)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(20, 10, 20, 10)

        self.branch_label = QLabel("📍 Немає репозиторію")
        self.branch_label.setStyleSheet("color: #e0e0e0; font-size: 16px; font-weight: bold;")
        hl.addWidget(self.branch_label)
        hl.addStretch()

        refresh_btn = QPushButton("🔄 Оновити")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #0e639c;
                color: white;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1177bb; }
        """)
        refresh_btn.clicked.connect(self.refresh_status)
        hl.addWidget(refresh_btn)

        layout.addWidget(header)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #1e1e1e;
            }
            QTabBar::tab {
                background-color: #2d2d30;
                color: #888;
                padding: 10px 20px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
        """)

        self.tabs.addTab(self.create_status_tab(), "📊 Статус")
        self.tabs.addTab(self.create_commit_tab(), "💬 Commit")
        self.tabs.addTab(self.create_history_tab(), "📜 Історія")
        self.tabs.addTab(self.create_branch_tab(), "🌿 Гілки")

        layout.addWidget(self.tabs)

    def create_status_tab(self):
        """Вкладка статусу"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        # Статус репозиторію
        self.status_info = QLabel()
        self.status_info.setStyleSheet("color: #888; padding: 10px;")
        layout.addWidget(self.status_info)

        # Списки змін
        splitter = QSplitter(Qt.Horizontal)

        # Staged changes
        staged_widget = QWidget()
        sl = QVBoxLayout(staged_widget)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.addWidget(QLabel("✅ Staged changes"))
        self.staged_list = QListWidget()
        self.staged_list.setStyleSheet("""
            QListWidget {
                background: #2a2a2e;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 6px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background: #0e639c;
            }
        """)
        sl.addWidget(self.staged_list)
        splitter.addWidget(staged_widget)

        # Unstaged changes
        unstaged_widget = QWidget()
        ul = QVBoxLayout(unstaged_widget)
        ul.setContentsMargins(0, 0, 0, 0)
        ul.addWidget(QLabel("📝 Unstaged changes"))
        self.unstaged_list = QListWidget()
        self.unstaged_list.setStyleSheet("""
            QListWidget {
                background: #2a2a2e;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
            }
        """)
        ul.addWidget(self.unstaged_list)
        splitter.addWidget(unstaged_widget)

        # Untracked files
        untracked_widget = QWidget()
        unl = QVBoxLayout(untracked_widget)
        unl.setContentsMargins(0, 0, 0, 0)
        unl.addWidget(QLabel("🆕 Untracked files"))
        self.untracked_list = QListWidget()
        self.untracked_list.setStyleSheet("""
            QListWidget {
                background: #2a2a2e;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
            }
        """)
        unl.addWidget(self.untracked_list)
        splitter.addWidget(untracked_widget)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 1)
        layout.addWidget(splitter)

        # Buttons
        btn_layout = QHBoxLayout()
        
        add_all_btn = QPushButton("➕ Add All")
        add_all_btn.setStyleSheet("background-color: #2d7d2d;")
        add_all_btn.clicked.connect(self.add_all)
        btn_layout.addWidget(add_all_btn)

        add_selected_btn = QPushButton("➕ Add Selected")
        add_selected_btn.setStyleSheet("background-color: #0e639c;")
        add_selected_btn.clicked.connect(self.add_selected)
        btn_layout.addWidget(add_selected_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return widget

    def create_commit_tab(self):
        """Вкладка комітів"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        # Commit message
        layout.addWidget(QLabel("💬 Повідомлення коміту:"))
        self.commit_message_edit = QLineEdit()
        self.commit_message_edit.setPlaceholderText("Введіть повідомлення коміту...")
        self.commit_message_edit.setStyleSheet("""
            QLineEdit {
                background: #2a2a2e;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
                padding: 10px;
                color: #d4d4d4;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #0078d4;
            }
        """)
        self.commit_message_edit.returnPressed.connect(self.make_commit)
        layout.addWidget(self.commit_message_edit)

        # Diff preview
        layout.addWidget(QLabel("📋 Зміни:"))
        self.diff_preview = QTextEdit()
        self.diff_preview.setReadOnly(True)
        self.diff_preview.setStyleSheet("""
            QTextEdit {
                background: #1a1a1a;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
                padding: 10px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.diff_preview)

        # Buttons
        btn_layout = QHBoxLayout()
        
        commit_btn = QPushButton("✅ Commit")
        commit_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d7d2d;
                color: white;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #3d8d3d; }
        """)
        commit_btn.clicked.connect(self.make_commit)
        btn_layout.addWidget(commit_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return widget

    def create_history_tab(self):
        """Вкладка історії"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        self.history_list = QListWidget()
        self.history_list.setStyleSheet("""
            QListWidget {
                background: #2a2a2e;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #3e3e3e;
            }
            QListWidget::item:selected {
                background: #0e639c;
            }
        """)
        self.history_list.itemDoubleClicked.connect(self.show_commit_details)
        layout.addWidget(self.history_list)

        # Buttons
        btn_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Оновити")
        refresh_btn.clicked.connect(self.load_history)
        btn_layout.addWidget(refresh_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return widget

    def create_branch_tab(self):
        """Вкладка гілок"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        # Current branches
        layout.addWidget(QLabel("📍 Існуючі гілки:"))
        self.branch_list = QListWidget()
        self.branch_list.setStyleSheet("""
            QListWidget {
                background: #2a2a2e;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
            }
        """)
        self.branch_list.itemDoubleClicked.connect(self.checkout_branch)
        layout.addWidget(self.branch_list)

        # Create new branch
        branch_layout = QHBoxLayout()
        branch_layout.addWidget(QLabel("🆕 Нова гілка:"))
        self.new_branch_edit = QLineEdit()
        self.new_branch_edit.setPlaceholderText("Назва гілки...")
        self.new_branch_edit.setStyleSheet("""
            QLineEdit {
                background: #2a2a2e;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
                padding: 8px;
                color: #d4d4d4;
            }
        """)
        branch_layout.addWidget(self.new_branch_edit)

        create_btn = QPushButton("Створити")
        create_btn.setStyleSheet("background-color: #0e639c;")
        create_btn.clicked.connect(self.create_branch)
        branch_layout.addWidget(create_btn)

        layout.addLayout(branch_layout)

        # Remote operations
        remote_group = QFrame()
        remote_group.setStyleSheet("QFrame { background: #252525; border-radius: 8px; }")
        remote_layout = QVBoxLayout(remote_group)
        remote_layout.setContentsMargins(12, 12, 12, 12)
        remote_layout.setSpacing(8)

        remote_layout.addWidget(QLabel("🌐 Remote operations:"))

        remote_btn_layout = QHBoxLayout()
        
        push_btn = QPushButton("⬆️ Push")
        push_btn.setStyleSheet("background-color: #2d7d2d;")
        push_btn.clicked.connect(self.push)
        remote_btn_layout.addWidget(push_btn)

        pull_btn = QPushButton("⬇️ Pull")
        pull_btn.setStyleSheet("background-color: #d6701e;")
        pull_btn.clicked.connect(self.pull)
        remote_btn_layout.addWidget(pull_btn)

        remote_btn_layout.addStretch()
        remote_layout.addLayout(remote_btn_layout)

        layout.addWidget(remote_group)
        layout.addStretch()

        return widget

    def refresh_status(self):
        """Оновити статус Git"""
        if not self.git.is_repo():
            self.branch_label.setText("📍 Немає репозиторію")
            self.branch_label.setStyleSheet("color: #f44747;")
            self.status_info.setText("💡 Натисніть 'Ініціалізувати' для створення Git репозиторію")
            return

        status = self.git.get_status()
        if status:
            self.branch_label.setText(f"📍 {status.branch}")
            
            if status.ahead > 0 or status.behind > 0:
                self.branch_label.setText(
                    f"📍 {status.branch} ({status.ahead}↑ {status.behind}↓)"
                )

            status_text = f"📊 "
            if status.is_clean:
                status_text += "Робоче дерево чисте"
            else:
                parts = []
                if status.staged:
                    parts.append(f"{len(status.staged)} staged")
                if status.unstaged:
                    parts.append(f"{len(status.unstaged)} unstaged")
                if status.untracked:
                    parts.append(f"{len(status.untracked)} untracked")
                status_text += " • ".join(parts)

            self.status_info.setText(status_text)

            # Заповнити списки
            self.staged_list.clear()
            for item in status.staged:
                self.staged_list.addItem(f"✅ {item}")

            self.unstaged_list.clear()
            for item in status.unstaged:
                self.unstaged_list.addItem(f"📝 {item}")

            self.untracked_list.clear()
            for item in status.untracked:
                self.untracked_list.addItem(f"🆕 {item}")

            # Оновити diff
            diff = self.git.get_diff()
            self.diff_preview.setText(diff if diff else "Немає змін")

            # Завантажити гілки та історію
            self.load_branches()
            self.load_history()

    def load_branches(self):
        """Завантажити список гілок"""
        branches = self.git.get_branches()
        self.branch_list.clear()
        for branch in branches:
            item = QListWidgetItem(f"🌿 {branch}")
            font = QFont()
            if branch == self.git.get_status().branch if self.git.get_status() else "":
                font.setBold(True)
                item.setForeground(Qt.green)
            item.setFont(font)
            self.branch_list.addItem(item)

    def load_history(self):
        """Завантажити історію комітів"""
        commits = self.git.get_log(20)
        self.history_list.clear()
        
        for commit in commits:
            date_str = commit.date[:10] if commit.date else "Unknown"
            item = QListWidgetItem(
                f"{commit.short_hash} | {commit.author} | {date_str}\n{commit.message}"
            )
            item.setFont(QFont("Consolas", 11))
            self.history_list.addItem(item)

    def add_all(self):
        """Додати всі зміни"""
        success, msg = self.git.add_all()
        QMessageBox.information(self, "Git", msg)
        self.refresh_status()

    def add_selected(self):
        """Додати вибрані файли"""
        for item in self.unstaged_list.selectedItems():
            file_path = item.text().replace("📝 ", "")
            success, msg = self.git.add_file(file_path)
        self.refresh_status()

    def make_commit(self):
        """Створити коміт"""
        message = self.commit_message_edit.text().strip()
        if not message:
            QMessageBox.warning(self, "Git", "Введіть повідомлення коміту")
            return

        # Спочатку додати всі зміни
        self.git.add_all()
        
        success, msg = self.git.commit(message)
        QMessageBox.information(self, "Git", msg)
        
        if success:
            self.commit_message_edit.clear()
            self.commit_made.emit(message)
            self.refresh_status()

    def show_commit_details(self, item):
        """Показати деталі коміту"""
        # TODO: Implement commit details view
        pass

    def checkout_branch(self, item):
        """Перемкнутися на гілку"""
        branch = item.text().replace("🌿 ", "")
        success, msg = self.git.checkout_branch(branch)
        QMessageBox.information(self, "Git", msg)
        self.refresh_status()

    def create_branch(self):
        """Створити нову гілку"""
        name = self.new_branch_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Git", "Введіть назву гілки")
            return

        success, msg = self.git.create_branch(name)
        QMessageBox.information(self, "Git", msg)
        self.new_branch_edit.clear()
        self.refresh_status()

    def push(self):
        """Push комітів"""
        reply = QMessageBox.question(
            self, "Push",
            "Ви впевнені, що хочете push-ити зміни?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, msg = self.git.push()
            QMessageBox.information(self, "Git", msg)
            self.refresh_status()

    def pull(self):
        """Pull змін"""
        reply = QMessageBox.question(
            self, "Pull",
            "Ви впевнені, що хочете pull-ити зміни?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, msg = self.git.pull()
            QMessageBox.information(self, "Git", msg)
            self.refresh_status()
