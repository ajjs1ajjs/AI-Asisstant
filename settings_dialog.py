"""
Settings Dialog для AI IDE
Діалог налаштувань з усіма опціями
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from settings import get_settings


class SettingsDialog(QDialog):
    """Діалог налаштувань додатку"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Налаштування")
        self.setModal(True)
        self.setMinimumSize(700, 600)
        self.resize(800, 700)
        self.settings = get_settings()
        self.setup_ui()
        self.load_settings()

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

        title = QLabel("⚙️ Налаштування")
        title.setStyleSheet("color: #e0e0e0; font-size: 18px; font-weight: bold;")
        hl.addWidget(title)
        hl.addStretch()
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
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            QTabBar::tab:hover {
                background-color: #3e3e3e;
                color: #e0e0e0;
            }
        """)

        self.tabs.addTab(self.create_model_tab(), "🧠 Модель")
        self.tabs.addTab(self.create_context_tab(), "📚 Контекст")
        self.tabs.addTab(self.create_chat_tab(), "💬 Чат")
        self.tabs.addTab(self.create_ui_tab(), "🎨 Інтерфейс")
        self.tabs.addTab(self.create_api_tab(), "🔑 API Keys")
        self.tabs.addTab(self.create_advanced_tab(), "🔧 Розширені")

        layout.addWidget(self.tabs)

        # Footer buttons
        footer = QFrame()
        footer.setFixedHeight(60)
        footer.setStyleSheet("""
            QFrame {
                background-color: #2d2d30;
                border-top: 1px solid #3e3e3e;
            }
        """)
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(20, 10, 20, 10)

        reset_btn = QPushButton("🔄 Скинути")
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a2525;
                color: #f44747;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #6a3535; }
        """)
        reset_btn.clicked.connect(self.reset_settings)
        fl.addWidget(reset_btn)
        fl.addStretch()

        cancel_btn = QPushButton("❌ Скасувати")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #3e3e3e;
                color: #d4d4d4;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #4e4e4e; }
        """)
        cancel_btn.clicked.connect(self.reject)
        fl.addWidget(cancel_btn)

        save_btn = QPushButton("💾 Зберегти")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #0e639c;
                color: white;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1177bb; }
        """)
        save_btn.clicked.connect(self.save_settings)
        fl.addWidget(save_btn)

        layout.addWidget(footer)

    def create_slider_row(self, label, min_val, max_val, value, suffix=""):
        """Створити рядок з слайдером"""
        widget = QFrame()
        widget.setStyleSheet("QFrame { background: transparent; }")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 4, 0, 4)

        lbl = QLabel(label)
        lbl.setStyleSheet("color: #d4d4d4; min-width: 150px;")
        layout.addWidget(lbl)

        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setValue(int(value * 100) if max_val <= 100 else int(value))
        slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: none;
                height: 6px;
                background: #3e3e3e;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #0078d4;
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #1177bb;
            }
        """)
        layout.addWidget(slider)

        spin = QDoubleSpinBox() if max_val <= 100 else QSpinBox()
        spin.setMinimum(min_val)
        spin.setMaximum(max_val)
        spin.setValue(value)
        spin.setSuffix(suffix)
        spin.setFixedWidth(100)
        spin.setStyleSheet("""
            QSpinBox, QDoubleSpinBox {
                background: #2a2a2e;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
                padding: 4px 8px;
                color: #d4d4d4;
            }
        """)
        
        def update_spin(val):
            spin.setValue(val / 100 if max_val <= 100 else val)
        def update_slider(val):
            slider.setValue(int(val * 100) if max_val <= 100 else int(val))
        
        slider.valueChanged.connect(update_spin)
        spin.valueChanged.connect(update_slider)
        
        layout.addWidget(spin)

        return widget, slider, spin

    def create_model_tab(self):
        """Вкладка налаштувань моделі"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)

        # Context size
        self.ctx_size_spin = QSpinBox()
        self.ctx_size_spin.setRange(512, 131072)  # До 128K
        self.ctx_size_spin.setSingleStep(1024)
        self.ctx_size_spin.setSuffix(" токенів")
        
        # GPU layers
        self.gpu_layers_spin = QSpinBox()
        self.gpu_layers_spin.setRange(0, 100)
        self.gpu_layers_spin.setSuffix(" шарів")

        # Temperature
        self.temp_slider = QSlider(Qt.Horizontal)
        self.temp_slider.setMinimum(0)
        self.temp_slider.setMaximum(100)
        
        # Max tokens
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(64, 32768)  # До 32K
        self.max_tokens_spin.setSingleStep(128)
        self.max_tokens_spin.setSuffix(" токенів")

        # Form layout
        self._form_row(layout, "📏 Розмір контексту:", self.ctx_size_spin)
        self._form_row(layout, "🎮 GPU шари:", self.gpu_layers_spin)
        self._form_row(layout, "🌡️ Температура:", self.temp_slider, "slider")
        self._form_row(layout, "📝 Макс токенів:", self.max_tokens_spin)

        # CPU threads
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 64)
        self.threads_spin.setSuffix(" потоків")
        self.threads_spin.setSpecialValueText("Авто")
        self._form_row(layout, "💻 CPU потоки:", self.threads_spin)

        layout.addStretch()
        scroll.setWidget(container)
        return scroll

    def _form_row(self, layout, label, widget, widget_type="spin"):
        row = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setStyleSheet("color: #d4d4d4; min-width: 150px;")
        row.addWidget(lbl)
        
        if widget_type == "slider":
            widget.setStyleSheet("""
                QSlider::groove:horizontal {
                    border: none;
                    height: 6px;
                    background: #3e3e3e;
                    border-radius: 3px;
                }
                QSlider::handle:horizontal {
                    background: #0078d4;
                    width: 16px;
                    margin: -5px 0;
                    border-radius: 8px;
                }
            """)
            row.addWidget(widget)
            val_lbl = QLabel("0.70")
            val_lbl.setStyleSheet("color: #0078d4; min-width: 40px;")
            widget.valueChanged.connect(lambda v: val_lbl.setText(f"{v/100:.2f}"))
            row.addWidget(val_lbl)
        else:
            widget.setStyleSheet("""
                QSpinBox {
                    background: #2a2a2e;
                    border: 1px solid #3e3e3e;
                    border-radius: 4px;
                    padding: 4px 8px;
                    color: #d4d4d4;
                }
            """)
            row.addWidget(widget)
            row.addStretch()
        
        layout.addLayout(row)

    def create_context_tab(self):
        """Вкладка контексту"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)

        # Embedding model
        self.embedding_combo = QComboBox()
        self.embedding_combo.addItems([
            "all-MiniLM-L6-v2 (384d, швидка)",
            "all-mpnet-base-v2 (768d, якісна)",
            "multi-qa-MiniLM-L6-cos-v1 (код)",
        ])
        self._form_row(layout, "🧠 Ембединг модель:", self.embedding_combo, "combo")

        # Chunk size
        self.chunk_size_spin = QSpinBox()
        self.chunk_size_spin.setRange(100, 1000)
        self.chunk_size_spin.setSingleStep(50)
        self._form_row(layout, "📄 Розмір чанку:", self.chunk_size_spin, "spin")

        # Overlap
        self.overlap_spin = QSpinBox()
        self.overlap_spin.setRange(0, 200)
        self._form_row(layout, "🔁 Overlap:", self.overlap_spin, "spin")

        # Max files
        self.max_files_spin = QSpinBox()
        self.max_files_spin.setRange(50, 2000)
        self.max_files_spin.setSingleStep(50)
        self._form_row(layout, "📁 Макс файлів:", self.max_files_spin, "spin")

        # Search results
        self.search_k_spin = QSpinBox()
        self.search_k_spin.setRange(1, 20)
        self._form_row(layout, "🔍 Результатів пошуку:", self.search_k_spin, "spin")

        # Auto index
        self.auto_index_chk = QCheckBox("Автоматично індексувати проект")
        self.auto_index_chk.setStyleSheet("color: #d4d4d4;")
        layout.addWidget(self.auto_index_chk)

        layout.addStretch()
        scroll.setWidget(container)
        return scroll

    def create_chat_tab(self):
        """Вкладка чату"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)

        # System prompt
        layout.addWidget(QLabel("🤖 System Prompt:"))
        self.system_prompt_edit = QTextEdit()
        self.system_prompt_edit.setMaximumHeight(100)
        self.system_prompt_edit.setStyleSheet("""
            QTextEdit {
                background: #2a2a2e;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
                padding: 8px;
                color: #d4d4d4;
            }
        """)
        layout.addWidget(self.system_prompt_edit)

        # Save history
        self.save_history_chk = QCheckBox("Зберігати історію чатів")
        self.save_history_chk.setStyleSheet("color: #d4d4d4;")
        layout.addWidget(self.save_history_chk)

        # Max history
        self.max_history_spin = QSpinBox()
        self.max_history_spin.setRange(10, 500)
        self._form_row(layout, "📚 Макс історії:", self.max_history_spin, "spin")

        # Stream response
        self.stream_chk = QCheckBox("Потоковий вивід відповідей")
        self.stream_chk.setStyleSheet("color: #d4d4d4;")
        layout.addWidget(self.stream_chk)

        layout.addStretch()
        scroll.setWidget(container)
        return scroll

    def create_ui_tab(self):
        """Вкладка інтерфейсу"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)

        # Theme
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light", "Blue", "Purple", "Green"])
        self._form_row(layout, "🎨 Тема:", self.theme_combo, "combo")

        # Font size
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(10, 24)
        self._form_row(layout, "📏 Розмір шрифту:", self.font_size_spin, "spin")

        # Sidebar width
        self.sidebar_spin = QSpinBox()
        self.sidebar_spin.setRange(150, 500)
        self.sidebar_spin.setSuffix(" px")
        self._form_row(layout, "📐 Ширина панелі:", self.sidebar_spin, "spin")

        # Auto scroll
        self.auto_scroll_chk = QCheckBox("Автопрокрутка чату")
        self.auto_scroll_chk.setStyleSheet("color: #d4d4d4;")
        layout.addWidget(self.auto_scroll_chk)

        layout.addStretch()
        scroll.setWidget(container)
        return scroll

    def create_api_tab(self):
        """Вкладка API keys"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(16)

        info = QLabel("🔑 API Keys для хмарних провайдерів (опціонально)")
        info.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(info)

        self.api_inputs = {}
        providers = [
            ("🆓 OpenRouter (Free)", "openrouter", "openrouter.ai"),
            ("🆓 HuggingFace", "huggingface", "huggingface.co"),
            ("🆓 Google AI Studio", "google", "aistudio.google.com"),
            ("💰 Groq (Free tier)", "groq", "groq.com"),
            ("💰 Together AI (Free)", "together", "together.xyz"),
            ("💰 DeepSeek", "deepseek", "deepseek.com"),
            ("💰 SiliconFlow", "siliconflow", "siliconflow.cn"),
        ]

        for name, key, url in providers:
            row = QVBoxLayout()
            row.addWidget(QLabel(f"{name} - {url}"))
            edit = QLineEdit()
            edit.setPlaceholderText(f"Введіть {name.split()[0]} API key")
            edit.setEchoMode(QLineEdit.Password)
            edit.setStyleSheet("""
                QLineEdit {
                    background: #2a2a2e;
                    border: 1px solid #3e3e3e;
                    border-radius: 4px;
                    padding: 8px 12px;
                    color: #d4d4d4;
                }
                QLineEdit:focus {
                    border: 1px solid #0078d4;
                }
            """)
            row.addWidget(edit)
            layout.addLayout(row)
            self.api_inputs[key] = edit

        layout.addStretch()
        scroll.setWidget(container)
        return scroll

    def create_advanced_tab(self):
        """Вкладка розширених налаштувань"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)

        # Use mmap
        self.mmap_chk = QCheckBox("Використовувати memory-mapped files (економія RAM)")
        self.mmap_chk.setStyleSheet("color: #d4d4d4;")
        layout.addWidget(self.mmap_chk)

        # Use mlock
        self.mlock_chk = QCheckBox("Lock в RAM (стабільніше, але повільніше)")
        self.mlock_chk.setStyleSheet("color: #d4d4d4;")
        layout.addWidget(self.mlock_chk)

        # Top P
        self.top_p_slider = QSlider(Qt.Horizontal)
        self.top_p_slider.setMinimum(0)
        self.top_p_slider.setMaximum(100)
        self.top_p_slider.setValue(90)
        self._form_row(layout, "🎯 Top P:", self.top_p_slider, "slider")

        # Top K
        self.top_k_spin = QSpinBox()
        self.top_k_spin.setRange(1, 100)
        self._form_row(layout, "🎯 Top K:", self.top_k_spin, "spin")

        # Repeat penalty
        self.repeat_penalty_slider = QSlider(Qt.Horizontal)
        self.repeat_penalty_slider.setMinimum(100)
        self.repeat_penalty_slider.setMaximum(200)
        self.repeat_penalty_slider.setValue(110)
        self._form_row(layout, "🔁 Repeat Penalty:", self.repeat_penalty_slider, "slider")

        layout.addStretch()
        scroll.setWidget(container)
        return scroll

    def load_settings(self):
        """Завантажити налаштування"""
        s = self.settings.settings

        # Model
        self.ctx_size_spin.setValue(s.model.n_ctx)
        self.gpu_layers_spin.setValue(s.model.n_gpu_layers)
        self.temp_slider.setValue(int(s.model.temperature * 100))
        self.max_tokens_spin.setValue(s.model.max_tokens)
        self.threads_spin.setValue(s.model.n_threads)

        # Context
        idx = self.embedding_combo.findText(s.context.embedding_model)
        if idx >= 0:
            self.embedding_combo.setCurrentIndex(idx)
        self.chunk_size_spin.setValue(s.context.chunk_size)
        self.overlap_spin.setValue(s.context.chunk_overlap)
        self.max_files_spin.setValue(s.context.max_context_files)
        self.search_k_spin.setValue(s.context.search_results)
        self.auto_index_chk.setChecked(s.context.auto_index)

        # Chat
        self.system_prompt_edit.setPlainText(s.chat.system_prompt)
        self.save_history_chk.setChecked(s.chat.save_history)
        self.max_history_spin.setValue(s.chat.max_history)
        self.stream_chk.setChecked(s.chat.stream_response)

        # UI
        idx = self.theme_combo.findText(s.ui.theme.capitalize())
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)
        self.font_size_spin.setValue(s.ui.font_size)
        self.sidebar_spin.setValue(s.ui.sidebar_width)
        self.auto_scroll_chk.setChecked(s.ui.auto_scroll)

        # API Keys
        for key, edit in self.api_inputs.items():
            edit.setText(self.settings.get_api_key(key) or "")

        # Advanced
        self.mmap_chk.setChecked(s.model.use_mmap)
        self.mlock_chk.setChecked(s.model.use_mlock)
        self.top_p_slider.setValue(int(s.model.top_p * 100))
        self.top_k_spin.setValue(s.model.top_k)
        self.repeat_penalty_slider.setValue(int(s.model.repeat_penalty * 100))

    def save_settings(self):
        """Зберегти налаштування"""
        s = self.settings.settings

        # Model
        s.model.n_ctx = self.ctx_size_spin.value()
        s.model.n_gpu_layers = self.gpu_layers_spin.value()
        s.model.temperature = self.temp_slider.value() / 100
        s.model.max_tokens = self.max_tokens_spin.value()
        s.model.n_threads = self.threads_spin.value()

        # Context
        s.context.embedding_model = self.embedding_combo.currentText().split()[0]
        s.context.chunk_size = self.chunk_size_spin.value()
        s.context.chunk_overlap = self.overlap_spin.value()
        s.context.max_context_files = self.max_files_spin.value()
        s.context.search_results = self.search_k_spin.value()
        s.context.auto_index = self.auto_index_chk.isChecked()

        # Chat
        s.chat.system_prompt = self.system_prompt_edit.toPlainText()
        s.chat.save_history = self.save_history_chk.isChecked()
        s.chat.max_history = self.max_history_spin.value()
        s.chat.stream_response = self.stream_chk.isChecked()

        # UI
        s.ui.theme = self.theme_combo.currentText().lower()
        s.ui.font_size = self.font_size_spin.value()
        s.ui.sidebar_width = self.sidebar_spin.value()
        s.ui.auto_scroll = self.auto_scroll_chk.isChecked()

        # API Keys
        for key, edit in self.api_inputs.items():
            if edit.text():
                self.settings.set_api_key(key, edit.text())

        # Advanced
        s.model.use_mmap = self.mmap_chk.isChecked()
        s.model.use_mlock = self.mlock_chk.isChecked()
        s.model.top_p = self.top_p_slider.value() / 100
        s.model.top_k = self.top_k_spin.value()
        s.model.repeat_penalty = self.repeat_penalty_slider.value() / 100

        self.settings.save()
        self.accept()

    def reset_settings(self):
        """Скинути налаштування"""
        reply = QMessageBox.question(
            self,
            "Скидання налаштувань",
            "Ви впевнені, що хочете скинути всі налаштування?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.settings.reset_to_defaults()
            self.load_settings()
