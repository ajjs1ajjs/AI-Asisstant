# Виправлення для main.py - додавання функціоналу аналізу проекту

# Знайдіть метод send() і замініть секцію code_analysis на:

"""
        is_code_analysis = any(p in text_lower for p in code_analysis_patterns)

        if is_code_analysis and self.project_path:
            # Збираємо інформацію про проект
            analysis_context = self._analyze_project_structure()
            
            # Додаємо контекст з context_engine
            ctx = (
                self.context_engine.get_context_for_query(text, k=10)
                if self.context_engine.chunks
                else ""
            )
            
            if analysis_context or ctx:
                # Формуємо повне повідомлення з контекстом
                full_context = "=== PROJECT STRUCTURE ===\n"
                if analysis_context:
                    full_context += analysis_context + "\n\n"
                if ctx:
                    full_context += "=== CODE CONTEXT ===\n" + ctx + "\n\n"
                
                full_context += "=== USER REQUEST ===\n" + text
                
                # Показуємо що йде аналіз
                self.chat.append(
                    "<div style='background: #2a3a2a; padding: 10px; border-radius: 8px; margin: 4px 0;'>"
                    "<span style='color: #4ec9b0;'>🔍 Аналіз проекту з " + str(len(self.context_engine.chunks)) + " чанків...</span></div>"
                )
                
                # Додаємо системний промпт
                system_prompt = "Ти - досвідчений розробник ПЗ. Ти аналізуєш код проекту. Надай детальний аналіз: структуру, мови програмування, архітектуру, потенційні проблеми, рекомендації щодо покращення. Завжди відповідай українською мовою."
                
                # Додаємо системний промпт на початок
                if not self.chat_history or self.chat_history[0].get("role") != "system":
                    self.chat_history.insert(0, {"role": "system", "content": system_prompt})
                
                self.chat_history.append({"role": "user", "content": full_context})
                
                # Запускаємо генерацію
                self.is_generating = True
                self.work_status.setText("Думає...")
                self.status_icon.setStyleSheet("color: #0078d4; font-size: 10px;")
                self.typing.start()
                
                # Генерація в окремому потоці
                import threading
                threading.Thread(target=self._generate_analysis_response, daemon=True).start()
                return  # Виходимо, не продовжуємо до звичайного send
"""

# Додайте новий метод після _analyze_project_structure:

"""
    def _generate_analysis_response(self):
        """Генерація відповіді для аналізу проекту"""
        try:
            response = self.inference.chat(self.chat_history, max_tokens=4096)
            self.chat_history.append({"role": "assistant", "content": response})
            
            # Показ відповіді
            from PySide6.QtCore import Qt
            self.chat.append(f"""<div style='background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #1a4a2a,stop:1 #2a5a3a);
                padding: 12px; border-radius: 12px; margin: 6px 0 6px 0;'>
                <div style='color: #4ec9b0; font-size: 11px; margin-bottom: 4px;'>🤖 Аналіз завершено:</div>
                <div style='color: #d4d4d4; font-size: 13px; white-space: pre-wrap;'>{response}</div>
            </div>""")
        except Exception as e:
            self.chat.append(f"<div style='color: #f44747;'>❌ Помилка аналізу: {e}</div>")
        finally:
            self.is_generating = False
            self.work_status.setText("Готовий")
            self.status_icon.setStyleSheet("color: #4ec9b0; font-size: 10px;")
            self.typing.stop()
"""
