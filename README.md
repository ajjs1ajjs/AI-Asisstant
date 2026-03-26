<<<<<<< HEAD
# 🧠 AI Coding IDE

Локальна AI IDE для програмування з підтримкою GGUF моделей (Qwen, Llama, DeepSeek, Phi-3, Mistral).

## ⚡ Особливості

- 🧠 **Локальні LLMs** - Працює без інтернету
- 📦 **Автозавантаження моделей** - Скачує GGUF з HuggingFace
- 💬 **Чат з контекстом** - AI відповідає на основі твого коду
- 📁 **Файл Explorer** - Навігація по проєкту
- 🧠 **Context Engine** - FAISS-based пошук по коду
- 🔀 **Git інтеграція** - commit, push, pull
- 🎨 **Темний UI** - Сучасний дизайн у стилі VS Code

## 🚀 Швидкий старт

### Варіант 1: Запуск з вихідників
```bash
pip install -r requirements.txt
python main.py
```

### Варіант 2: Готовий exe
```bash
# Завантаж AI_Coding_IDE.exe з релізів
# Або з папки dist/
```

## 📋 Вибір моделі

Рекомендовані моделі для кодування:

| Модель | Розмір | RAM | Призначення |
|--------|--------|-----|-------------|
| Qwen2.5-Coder-7B | 4.7 GB | 8 GB | 🏆 Найкраща для коду |
| Qwen2.5-Coder-14B | 9.1 GB | 16 GB | Краща якість |
| DeepSeek-Coder-6.7B | 4.2 GB | 8 GB | Чудово для коду |
| Llama-3.2-3B | 2.1 GB | 4 GB | Швидка для слабких ПК |

## 📂 Структура проєкту

```
├── main.py              # GUI додаток
├── model_manager.py    # Менеджер моделей
├── local_engine.py     # Llama-cpp-python інтеграція
├── context_engine.py   # FAISS контекстний пошук
├── ai_ide.spec         # PyInstaller конфіг
├── dist/               # Скомпільований exe
└── requirements.txt    # Залежності
```

## 💾 Збереження

- Моделі: `~/.ai-ide/models/`
- Конфіг: `~/.ai-ide/config.json`

## 🔧 Технології

- **GUI**: PySide6
- **LLM**: llama-cpp-python
- **Пошук**: FAISS
- **Білд**: PyInstaller

## 📝 Ліцензія

MIT
=======
# AI-Asisstant
>>>>>>> b7c284e3aeca614d81e6fa86d6f41e1636c07109
