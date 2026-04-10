import os
import subprocess
import sys

def build():
    print("Starting AI Coding IDE v6.0 EXE Build Process...")
    
    # 1. Clean previous builds
    if os.path.exists("build"):
        import shutil
        shutil.rmtree("build")
    if os.path.exists("dist"):
        import shutil
        shutil.rmtree("dist")

    # 2. Define PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--icon=icon.ico",
        "--name=AI_IDE_v6.0",
        
        # Paths
        "--paths=.",
        
        # Add Data
        "--add-data=ui/;ui/",
        "--add-data=core/;core/",
        "--add-data=plugins/;plugins/",
        "--add-data=style.qss;.",
        
        # Hidden Imports (Root Modules)
        "--hidden-import=agent_tools",
        "--hidden-import=git_integration",
        "--hidden-import=orchestrator",
        "--hidden-import=local_engine",
        "--hidden-import=model_manager",
        "--hidden-import=context_engine",
        "--hidden-import=autocomplete",
        "--hidden-import=settings",
        
        # Hidden Imports (Wave 6)
        "--hidden-import=fastapi",
        "--hidden-import=uvicorn",
        "--hidden-import=zeroconf",
        "--hidden-import=pandas",
        "--hidden-import=matplotlib",
        "--hidden-import=pyscreenshot",
        "--hidden-import=speech_recognition",
        "--hidden-import=deep_translator",
        
        # Main file
        "main.py"
    ]

    print(f"Executing: {' '.join(cmd)}")
    
    try:
        subprocess.check_call(cmd)
        print("\nBuild Successful! Check the 'dist/AI_IDE_v6.0' directory.")
    except Exception as e:
        print(f"\nBuild Failed: {e}")

if __name__ == "__main__":
    # Ensure recursion limit is high for large apps
    sys.setrecursionlimit(5000)
    build()
