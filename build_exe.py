import os
import shutil
import PyInstaller.__main__

def build():
    print("Building portable onedir build...")
    
    # Очищення
    if os.path.exists("dist"): shutil.rmtree("dist")
    if os.path.exists("build"): shutil.rmtree("build")

    # Збираємо всі .py файли з кореня та підпапок для впевненості
    # Це вирішить проблему ModuleNotFoundError
    datas = [
        ('ui/', 'ui/'),
        ('core/', 'core/'),
        ('plugins/', 'plugins/'),
        ('threads/', 'threads/'),
        ('style.qss', '.'),
        ('icon.ico', '.'),
    ]
    
    # Додаємо всі .py файли з кореня
    for f in os.listdir('.'):
        if f.endswith('.py') and f != 'build_exe.py':
            datas.append((f, '.'))

    params = [
        'main.py',
        '--noconfirm',
        '--onedir',          # Швидкий запуск
        '--windowed',
        '--icon=icon.ico',
        '--name=AI_IDE_v6.0',
        '--collect-all=llama_cpp',
        '--collect-all=faiss',
        '--collect-all=sentence_transformers',
    ]
    
    # Додаємо всі дані
    for src, dst in datas:
        params.append(f'--add-data={src};{dst}')
    
    PyInstaller.__main__.run(params)
    print("Build completed in 'dist/AI_IDE_v6.0'")

if __name__ == "__main__":
    build()
