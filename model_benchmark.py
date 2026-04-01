"""
Model Benchmark Module
Тестування продуктивності та якості моделей
"""

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class BenchmarkResult:
    """Результат бенчмарку"""
    model_name: str
    model_path: str
    date: str
    
    # Швидкість
    tokens_per_second: float
    load_time_seconds: float
    
    # Якість (суб'єктивна оцінка 1-10)
    quality_score: float = 0.0
    
    # Налаштування
    n_ctx: int = 2048
    n_gpu_layers: int = 0
    temperature: float = 0.7
    
    # Апаратне забезпечення
    ram_gb: float = 0.0
    cpu_cores: int = 0
    gpu_name: str = ""
    
    # Тестові завдання
    code_completion_score: float = 0.0
    chat_quality_score: float = 0.0
    reasoning_score: float = 0.0


class ModelBenchmark:
    """Бенчмарк для LLM моделей"""

    BENCHMARK_FILE = Path.home() / ".ai-ide" / "benchmarks.json"

    # Тестові завдання
    CODE_COMPLETION_PROMPT = """
Complete the Python function:

def fibonacci(n: int) -> List[int]:
    \"\"\"Generate first n Fibonacci numbers.\"\"\"
    if n <= 0:
        return []
    if n == 1:
        return [0]
    
    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    return fib

# Test the function
print(fibonacci(10))
"""

    CHAT_PROMPT = """
Explain the difference between '==' and 'is' in Python.
Provide a clear example showing when they give different results.
"""

    REASONING_PROMPT = """
A bat and a ball cost $1.10 in total.
The bat costs $1.00 more than the ball.
How much does the ball cost?

Show your reasoning step by step.
"""

    def __init__(self, inference_engine):
        self.inference = inference_engine
        self.results: List[BenchmarkResult] = []
        self._load_results()

    def _load_results(self):
        """Завантажити збережені результати"""
        if self.BENCHMARK_FILE.exists():
            try:
                with open(self.BENCHMARK_FILE, "r") as f:
                    data = json.load(f)
                self.results = [BenchmarkResult(**r) for r in data]
            except:
                pass

    def _save_results(self):
        """Зберегти результати"""
        self.BENCHMARK_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = [
            {
                "model_name": r.model_name,
                "model_path": r.model_path,
                "date": r.date,
                "tokens_per_second": r.tokens_per_second,
                "load_time_seconds": r.load_time_seconds,
                "quality_score": r.quality_score,
                "n_ctx": r.n_ctx,
                "n_gpu_layers": r.n_gpu_layers,
                "temperature": r.temperature,
                "ram_gb": r.ram_gb,
                "cpu_cores": r.cpu_cores,
                "gpu_name": r.gpu_name,
                "code_completion_score": r.code_completion_score,
                "chat_quality_score": r.chat_quality_score,
                "reasoning_score": r.reasoning_score,
            }
            for r in self.results
        ]
        with open(self.BENCHMARK_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def _get_system_info(self) -> Dict:
        """Отримати інформацію про систему"""
        import psutil

        ram_gb = psutil.virtual_memory().total / (1024**3)
        cpu_cores = psutil.cpu_count(logical=False) or os.cpu_count() or 1

        gpu_name = ""
        try:
            # Спроба отримати GPU інформацію
            import subprocess
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                gpu_name = result.stdout.strip().split("\n")[0]
        except:
            pass

        return {
            "ram_gb": round(ram_gb, 1),
            "cpu_cores": cpu_cores,
            "gpu_name": gpu_name
        }

    def run_speed_test(
        self,
        model_path: str,
        model_name: str,
        n_ctx: int = 2048,
        n_gpu_layers: int = 0,
        temperature: float = 0.7,
        test_tokens: int = 200
    ) -> BenchmarkResult:
        """
        Провести тест швидкості

        Args:
            model_path: Шлях до моделі
            model_name: Назва моделі
            n_ctx: Розмір контексту
            n_gpu_layers: GPU шари
            temperature: Температура
            test_tokens: Кількість токенів для тесту
        """
        print(f"\n🚀 Бенчмарк: {model_name}")
        print(f"   Шлях: {model_path}")
        print(f"   Налаштування: ctx={n_ctx}, gpu={n_gpu_layers}, temp={temperature}")

        sys_info = self._get_system_info()

        # Завантаження моделі
        print("\n📥 Завантаження моделі...")
        load_start = time.time()
        
        try:
            self.inference.load_model(
                model_path=model_path,
                n_ctx=n_ctx,
                n_gpu_layers=n_gpu_layers,
            )
            load_time = time.time() - load_start
            print(f"✅ Завантажено за {load_time:.1f}с")
        except Exception as e:
            print(f"❌ Помилка завантаження: {e}")
            return None

        # Тест генерації
        print(f"\n⚡ Тест швидкості ({test_tokens} токенів)...")
        
        prompt = "Write a Python function to check if a number is prime."
        
        gen_start = time.time()
        
        try:
            # Використати streaming для підрахунку токенів
            token_count = 0
            for token in self.inference.chat_stream(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=test_tokens,
                temperature=temperature
            ):
                token_count += 1
                if token_count >= test_tokens:
                    break
            
            gen_time = time.time() - gen_start
            tokens_per_second = token_count / gen_time if gen_time > 0 else 0
            
            print(f"   Згенеровано {token_count} токенів за {gen_time:.1f}с")
            print(f"   📊 Швидкість: {tokens_per_second:.1f} токенів/с")
            
        except Exception as e:
            print(f"⚠️ Помилка генерації: {e}")
            tokens_per_second = 0

        # Створити результат
        result = BenchmarkResult(
            model_name=model_name,
            model_path=model_path,
            date=datetime.now().isoformat(),
            tokens_per_second=round(tokens_per_second, 2),
            load_time_seconds=round(load_time, 2),
            n_ctx=n_ctx,
            n_gpu_layers=n_gpu_layers,
            temperature=temperature,
            ram_gb=sys_info["ram_gb"],
            cpu_cores=sys_info["cpu_cores"],
            gpu_name=sys_info["gpu_name"]
        )

        # Зберегти
        self.results.append(result)
        self._save_results()

        print(f"\n✅ Бенчмарк завершено!")
        print(f"   Швидкість: {tokens_per_second:.1f} tok/s")
        print(f"   Завантаження: {load_time:.1f}s")

        return result

    def run_quality_test(
        self,
        task: str = "all",
        max_tokens: int = 512
    ) -> Dict[str, float]:
        """
        Тест якості (суб'єктивна оцінка)

        Користувач оцінює відповіді від 1 до 10
        """
        if not self.inference.is_loaded:
            print("❌ Модель не завантажена")
            return {}

        scores = {}
        prompts = {}

        if task in ["code", "all"]:
            prompts["code_completion"] = self.CODE_COMPLETION_PROMPT
        if task in ["chat", "all"]:
            prompts["chat"] = self.CHAT_PROMPT
        if task in ["reasoning", "all"]:
            prompts["reasoning"] = self.REASONING_PROMPT

        for name, prompt in prompts.items():
            print(f"\n📝 Тест: {name}")
            print("-" * 50)
            
            try:
                response = self.inference.chat(
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=0.7
                )
                
                print(f"\n{response}\n")
                print("-" * 50)
                
                # Запитати оцінку
                while True:
                    try:
                        score = float(input(f"Оцініть якість {name} (1-10): "))
                        if 1 <= score <= 10:
                            scores[name] = score
                            break
                        print("Будь ласка, введіть число від 1 до 10")
                    except ValueError:
                        print("Будь ласка, введіть число")
                        
            except Exception as e:
                print(f"❌ Помилка: {e}")
                scores[name] = 0

        return scores

    def get_best_model(
        self,
        criterion: str = "speed"
    ) -> Optional[BenchmarkResult]:
        """
        Отримати найкращу модель за критерієм

        Args:
            criterion: 'speed', 'load_time', 'quality', 'balanced'
        """
        if not self.results:
            return None

        if criterion == "speed":
            return max(self.results, key=lambda r: r.tokens_per_second)
        elif criterion == "load_time":
            return min(self.results, key=lambda r: r.load_time_seconds)
        elif criterion == "quality":
            return max(self.results, key=lambda r: r.quality_score)
        elif criterion == "balanced":
            # Комбінований рейтинг
            for r in self.results:
                if r.tokens_per_second > 0:
                    r.quality_score = (
                        r.tokens_per_second * 0.5 +
                        r.code_completion_score * 2 +
                        r.chat_quality_score * 2 +
                        r.reasoning_score * 2
                    )
            return max(self.results, key=lambda r: r.quality_score)

        return None

    def get_all_results(self) -> List[BenchmarkResult]:
        """Отримати всі результати"""
        return self.results

    def clear_results(self):
        """Очистити результати"""
        self.results.clear()
        if self.BENCHMARK_FILE.exists():
            self.BENCHMARK_FILE.unlink()
        print("🗑️ Результати бенчмарків очищено")

    def export_results(self, path: str) -> bool:
        """Експортувати результати у CSV"""
        try:
            import csv
            
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Model", "Date", "Tokens/s", "Load Time",
                    "Code Score", "Chat Score", "Reasoning Score",
                    "RAM", "CPU", "GPU"
                ])
                
                for r in self.results:
                    writer.writerow([
                        r.model_name,
                        r.date[:10],
                        r.tokens_per_second,
                        f"{r.load_time_seconds:.1f}s",
                        r.code_completion_score,
                        r.chat_quality_score,
                        r.reasoning_score,
                        f"{r.ram_gb:.1f}GB",
                        r.cpu_cores,
                        r.gpu_name or "CPU"
                    ])
            return True
        except Exception as e:
            print(f"❌ Помилка експорту: {e}")
            return False
