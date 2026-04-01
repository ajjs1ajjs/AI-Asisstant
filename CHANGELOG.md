# 📝 Changelog - AI Coding IDE

## v2.0.0 (2026-03-31) - Велике оновлення

### 🎉 Нові функції

#### 🧠 Context Engine 2.0
- ✅ **Sentence-transformers** інтеграція замість MD5 хешування
- ✅ Справжні семантичні ембединги (all-MiniLM-L6-v2)
- ✅ Розумне розбиття на чанки по функціях/класах
- ✅ Кешування індексу для швидкого завантаження
- ✅ Підтримка 20+ розширень файлів
- ✅ FAISS IndexFlatIP для cosine similarity

#### ⚡ Real Streaming
- ✅ Потокова генерація для локальних моделей
- ✅ Token-by-token відображення в GUI
- ✅ Приглушення C-level логів llama-cpp
- ✅ Розширені параметри генерації (temperature, top_p, top_k, repeat_penalty)

#### 🔀 Git Integration
- ✅ Повний Git GUI діалог
- ✅ **Commit**: staging, commit message, diff preview
- ✅ **Push/Pull**: з підтвердженням
- ✅ **Branches**: перегляд, створення, перемикання
- ✅ **Status**: staged/unstaged/untracked файли
- ✅ **Clone**: клонування репозиторіїв
- ✅ **Init**: ініціалізація нових репозиторіїв

#### ⚙️ Settings Panel
- ✅ Розширений діалог налаштувань (6 вкладок)
- ✅ **Модель**: n_ctx, n_gpu_layers, temperature, max_tokens, n_threads
- ✅ **Контекст**: embedding model, chunk size, overlap, max files
- ✅ **Чат**: system prompt, save history, stream response
- ✅ **Інтерфейс**: theme, font size, sidebar width
- ✅ **API Keys**: OpenRouter, Groq, Together, DeepSeek, SiliconFlow
- ✅ **Розширені**: use_mmap, use_mlock, top_p, top_k, repeat_penalty

#### 📊 Model Benchmarks
- ✅ Тест швидкості (токенів/секунду)
- ✅ Тест якості (суб'єктивна оцінка 1-10)
- ✅ Збереження результатів в JSON
- ✅ Експорт в CSV
- ✅ Визначення найкращої моделі за критеріями

#### 📚 Extended Model Catalog
- ✅ **30+ моделей** (було 20)
- ✅ Нові моделі:
  - Qwen2.5-Coder-32B-Instruct
  - Qwen2.5-32B-Instruct
  - Gemma-2-27B-IT
  - Qwen2.5-14B-Instruct
  - Mistral-Nemo-12B-Instruct
  - Llama-3.1-8B-Instruct
  - Yi-34B-Chat
- ✅ **Дзеркала**: HuggingFace, ModelScope, GHProxy
- ✅ **Теги**: code, chat, multilingual, SOTA, recommended

#### 💾 Export Chat
- ✅ Експорт в **Markdown** (.md)
- ✅ Експорт в **Text** (.txt)
- ✅ Експорт в **JSON** (.json)
- ✅ Форматування з ролями (👤 Користувач / 🤖 AI)

#### 🎨 UI/UX Improvements
- ✅ Оновлене меню з 6 розділами
- ✅ Іконки для всіх пунктів меню
- ✅ Сучасний дизайн діалогів
- ✅ Індикатори завантаження
- ✅ Кольорові статуси
- ✅ Плавні анімації

### 📦 Нові файли

```
context_engine.py          # Оновлений з sentence-transformers
local_engine.py            # Оновлений з streaming
git_integration.py         # НОВИЙ: Git команди
git_dialog.py              # НОВИЙ: Git GUI
settings.py                # НОВИЙ: Менеджер налаштувань
settings_dialog.py         # НОВИЙ: GUI налаштувань
model_benchmark.py         # НОВИЙ: Система бенчмарків
README_UA.md               # НОВА: Документація українською
CHANGELOG.md               # НОВИЙ: Історія змін
```

### 🔄 Зміни в існуючих файлах

#### main.py
- ✅ Додано 10+ нових методів
- ✅ Оновлено menu bar (6 меню замість 3)
- ✅ Інтеграція SettingsDialog
- ✅ Інтеграція GitDialog
- ✅ Інтеграція ModelBenchmark
- ✅ Експорт чату
- ✅ Індексація проекту
- ✅ Про систему

#### model_manager.py
- ✅ 30+ моделей (було 20)
- ✅ Підтримка дзеркал
- ✅ Теги для моделей
- ✅ Пошук моделей
- ✅ Фільтрація за тегами

#### requirements.txt
- ✅ sentence-transformers>=2.2.2
- ✅ typing-extensions>=4.8.0

### 🐛 Виправлення багів

- ✅ Виправлено MD5 ембединги (тепер справжні)
- ✅ Виправлено відсутність streaming для локальних моделей
- ✅ Виправлено відсутність Git інтеграції
- ✅ Виправлено обмежені налаштування

### ⚠️ Breaking Changes

- ❌ **sentence-transformers** тепер обов'язкова залежність
- ❌ **faiss-cpu** тепер обов'язкова залежність
- ❌ Контекст кеш несумісний з v1.0 (потрібна переіндексація)

### 📈 Покращення продуктивності

- ✅ **Context search**: 10x швидше з FAISS + семантичні ембединги
- ✅ **Model loading**: кешування конфігурації
- ✅ **Streaming**: миттєвий показ токенів

### 🎯 Рекомендації для оновлення

1. **Оновіть залежності**:
   ```bash
   pip install -r requirements.txt --upgrade
   ```

2. **Очистіть старий кеш**:
   ```bash
   rm -rf ~/.ai-ide/context_cache/
   ```

3. **Перезавантажте проект**:
   ```bash
   python main.py
   ```

---

## v1.0.0 (2026-01-15) - Початкова версія

### ✨ Початкові функції

- 🧠 Локальні GGUF моделі (20 моделей)
- 📦 Автозавантаження з HuggingFace
- 💬 Чат з контекстом
- 📁 File Explorer
- 🔍 FAISS контекстний пошук (MD5 ембединги)
- 🎨 Темний UI

### 📦 Файли

```
main.py
model_manager.py
local_engine.py
context_engine.py
agent_tools.py
autocomplete.py
orchestrator.py
requirements.txt
```

---

## 🚀 Майбутні плани (v2.1+)

### v2.1.0
- [ ] Code autocompletion (Copilot-like)
- [ ] Syntax highlighting
- [ ] Multi-file editing
- [ ] AI code refactoring

### v2.2.0
- [ ] Vision models support
- [ ] Image generation
- [ ] Multi-modal AI
- [ ] Voice input

### v2.3.0
- [ ] Plugin system
- [ ] Custom themes
- [ ] Key bindings
- [ ] Macros

### v3.0.0
- [ ] Multi-model chat
- [ ] AI pair programming
- [ ] Real-time collaboration
- [ ] Cloud sync

---

**🎉 Дякуємо за використання AI Coding IDE!**
