# 🧠 AI Coding IDE

Локальна AI IDE з підтримкою GGUF моделей, хмарних провайдерів (Groq, OpenRouter, DeepSeek, Qwen), семантичного пошуку по коду та Git інтеграції.

## ✨ Можливості

| Функція | Опис |
|---------|------|
| 🧠 **Локальні LLM** | 30+ GGUF моделей — працює без інтернету |
| ☁️ **Хмарні провайдери** | Groq, OpenRouter, DeepSeek, Qwen, SiliconFlow |
| 📝 **Streaming статус** | Бачиш що робить AI: модель, токени, інструменти |
| 📁 **Context Engine** | FAISS семантичний пошук по кодовій базі |
| 🛠️ **Agent Tools** | AI читає/пише файли, виконує команди |
| 🔀 **Git інтеграція** | Commit, push, pull, branches прямо з IDE |
| 🎨 **Темний UI** | Стиль VS Code, drag-and-drop файлів |
| 🔒 **Безпека** | Білий список команд, валідація API ключів |

## 🚀 Швидкий старт

### Варіант 1: Запуск з вихідників

```bash
# Клонуй репозиторій
git clone https://github.com/ajjs1ajjs/AI-Asisstant.git
cd AI-Asisstant

# Встанови залежності
pip install -r requirements.txt

# Запусти
python main.py
```

### Варіант 2: Зібрати свій `.exe`

```bash
# 1. Встанови PyInstaller
pip install pyinstaller

# 2. Збери exe
pyinstaller ai_ide.spec --clean --noconfirm

# 3. Готовий exe буде в:
#    dist/AI_Coding_IDE_v2/AI_Coding_IDE_v2.exe
```

> ⏱️ Білд займає ~7 хвилин через велику кількість залежностей (PySide6, llama-cpp, FAISS).

## 📋 Рекомендовані моделі

| Модель | Розмір | RAM | Призначення |
|--------|--------|-----|-------------|
| Qwen2.5-Coder-7B | 4.7 GB | 8 GB | 🏆 Найкраща для коду |
| Qwen2.5-Coder-14B | 9.1 GB | 16 GB | Краща якість |
| DeepSeek-Coder-6.7B | 4.2 GB | 8 GB | Чудово для коду |
| Llama-3.2-3B | 2.1 GB | 4 GB | Швидка для слабких ПК |

## 🔑 Налаштування API ключів

Для хмарних провайдерів скопіюй `.env.example` → `.env` і встав свої ключі:

```bash
copy .env.example .env
```

Відкрий `.env` і заповни потрібні ключі:
```
GROQ_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here
DEEPSEEK_API_KEY=your_key_here
```

## 📂 Структура проекту

```
├── main.py              # Точка входу, PySide6 GUI
├── orchestrator.py      # Мульти-провайдер LLM (6 провайдерів)
├── model_manager.py     # Каталог 30+ GGUF моделей, завантаження
├── local_engine.py      # llama-cpp-python інференс
├── context_engine.py    # FAISS семантичний пошук по коду
├── agent_tools.py       # Інструменти агента (read/write file, run command)
├── autocomplete.py      # Copilot-like автодоповнення
├── settings.py          # Збереження конфігу
├── git_integration.py   # Git команди
├── ai_ide.spec          # PyInstaller конфіг для білду
├── requirements.txt     # Python залежності
├── ui/
│   ├── main_window.py   # Головне вікно
│   └── components.py    # UI компоненти (бульбашки, дерево файлів)
├── threads/
│   └── workers.py       # Async worker для streaming
└── tests/
    └── test_core.py     # 31 unit тест
```

## 💾 Збереження

| Що | Де |
|----|-----|
| Моделі | `~/.ai-ide/models/` |
| Конфіг | `~/.ai-ide/settings.json` |
| FAISS кеш | `~/.ai-ide/context_cache/` |

## 🧪 Тести

```bash
pip install pytest
pytest tests/test_core.py -v
```

## 🔧 Технології

| Компонент | Технологія |
|-----------|-----------|
| GUI | PySide6 |
| LLM | llama-cpp-python |
| Пошук | FAISS + sentence-transformers |
| HTTP | httpx |
| Білд | PyInstaller |
| Тести | pytest |

## 📝 Ліцензія

MIT
