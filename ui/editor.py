from PySide6.QtCore import Qt, Signal, QFileInfo
from PySide6.QtGui import (
    QFont,
    QTextCharFormat,
    QColor,
    QSyntaxHighlighter,
    QTextCursor,
)
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QPlainTextEdit,
    QSplitter,
    QTabWidget,
    QMessageBox,
    QFileDialog,
)

try:
    from PySide6.Qsci import QsciLexer, QsciScintilla

    SCINTILLA_AVAILABLE = True
except ImportError:
    SCINTILLA_AVAILABLE = False


class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent):
        super().__init__(parent)
        self._rules = []

        keywords = [
            "def",
            "class",
            "if",
            "else",
            "elif",
            "for",
            "while",
            "return",
            "import",
            "from",
            "as",
            "try",
            "except",
            "finally",
            "with",
            "pass",
            "break",
            "continue",
            "True",
            "False",
            "None",
            "and",
            "or",
            "not",
            "in",
            "is",
            "lambda",
            "yield",
            "raise",
            "assert",
            "global",
            "nonlocal",
            "del",
            "async",
            "await",
        ]
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#c586c0"))
        keyword_format.setFontWeight(QFont.Bold)
        for kw in keywords:
            self._rules.append((rf"\b{kw}\b", keyword_format))

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))
        self._rules.append((r"'''.*?'''", string_format))
        self._rules.append((r'""".*?"""', string_format))
        self._rules.append((r"'[^']*'", string_format))
        self._rules.append((r'"[^"]*"', string_format))

        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b5cea8"))
        self._rules.append((r"\b\d+\.?\d*\b", number_format))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6a9955"))
        self._rules.append((r"#.*", comment_format))

        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#dcdcaa"))
        self._rules.append((r"\b\w+(?=\()", function_format))

        decorator_format = QTextCharFormat()
        decorator_format.setForeground(QColor("#d7ba7d"))
        self._rules.append((r"@\w+", decorator_format))

    def highlightBlock(self, text):
        for pattern, fmt in self._rules:
            import re

            for match in re.finditer(pattern, text):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, fmt)


class CodeEditor(QWidget):
    file_saved = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file = None
        self.modified = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        toolbar = QHBoxLayout()
        self.file_label = QLabel("Untitled")
        toolbar.addWidget(self.file_label)
        toolbar.addStretch()

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_file)
        toolbar.addWidget(save_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close_tab)
        toolbar.addWidget(close_btn)

        layout.addLayout(toolbar)

        if SCINTILLA_AVAILABLE:
            self.editor = QsciScintilla()
            from PySide6.Qsci import QsciLexerPython

            self.editor.setLexer(QsciLexerPython())
        else:
            self.editor = QPlainTextEdit()
            self.highlighter = PythonHighlighter(self.editor.document())

        self.editor.setFont(QFont("Consolas", 11))
        self.editor.textChanged.connect(self.on_text_changed)

        layout.addWidget(self.editor)

    def on_text_changed(self):
        if not self.modified:
            self.modified = True
            self.update_title()

    def update_title(self):
        name = os.path.basename(self.current_file) if self.current_file else "Untitled"
        mark = " *" if self.modified else ""
        self.file_label.setText(name + mark)

    def load_file(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.editor.setPlainText(content)
            self.current_file = path
            self.modified = False
            self.update_title()
            return True
        except Exception as e:
            QMessageBox.warning(self, "Помилка", f"Не вдалося відкрити файл: {e}")
            return False

    def save_file(self):
        if not self.current_file:
            path, _ = QFileDialog.getSaveFileName(
                self, "Save file", "", "All files (*)"
            )
            if not path:
                return
            self.current_file = path

        try:
            content = self.editor.toPlainText()
            with open(self.current_file, "w", encoding="utf-8") as f:
                f.write(content)
            self.modified = False
            self.update_title()
            self.file_saved.emit(self.current_file)
        except Exception as e:
            QMessageBox.warning(self, "Помилка", f"Не вдалося зберегти: {e}")

    def close_tab(self):
        if self.modified:
            reply = QMessageBox.question(
                self,
                "Зберегти зміни?",
                "Файл змінено. Зберегти?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            )
            if reply == QMessageBox.Save:
                self.save_file()
            elif reply == QMessageBox.Cancel:
                return
        self.deleteLater()


import os


class EditorTabs(QTabWidget):
    file_opened = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.close_tab)
        self.files = {}

    def open_file(self, path):
        if path in self.files:
            self.setCurrentWidget(self.files[path])
            return

        editor = CodeEditor()
        if editor.load_file(path):
            name = os.path.basename(path)
            self.addTab(editor, name)
            self.setCurrentWidget(editor)
            self.files[path] = editor
            editor.file_saved.connect(self.on_file_saved)

    def on_file_saved(self, path):
        name = os.path.basename(path)
        idx = self.indexOf(self.files[path])
        if idx >= 0:
            self.setTabText(idx, name)

    def close_tab(self, index):
        widget = self.widget(index)
        if widget and hasattr(widget, "close_tab"):
            widget.close_tab()
            if widget.current_file in self.files:
                del self.files[widget.current_file]
            self.removeTab(index)
