"""
Rhizome Application Entry Point for PyInstaller
"""
import os
import sys
import subprocess
import threading
import webbrowser
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def check_env_file():
    base_path = get_base_path()
    env_path = os.path.join(base_path, '.env')
    env_example_path = os.path.join(base_path, '.env.example')
    
    if not os.path.exists(env_path):
        if os.path.exists(env_example_path):
            import shutil
            shutil.copy(env_example_path, env_path)
            logger.info("Created .env from .env.example")
            return False
    return True


def start_backend():
    base_path = get_base_path()
    os.chdir(base_path)
    
    if getattr(sys, 'frozen', False):
        backend_path = os.path.join(base_path, 'backend', 'main.py')
    else:
        backend_path = os.path.join(base_path, 'backend', 'main.py')
    
    subprocess.run([sys.executable, '-m', 'uvicorn', 'backend.main:app', '--host', '0.0.0.0', '--port', '8000'])


def open_browser():
    time.sleep(3)
    webbrowser.open('http://localhost:8000')


def main():
    print("=" * 50)
    print("  Rhizome - 知识体系智能助手")
    print("=" * 50)
    print()
    
    env_exists = check_env_file()
    if not env_exists:
        print("[提示] 已创建 .env 配置文件")
        print("[提示] 请编辑 .env 文件配置您的 API 密钥")
        print()
    
    print("[信息] 正在启动服务...")
    print("[信息] 服务启动后，浏览器将自动打开 http://localhost:8000")
    print("[信息] 按 Ctrl+C 停止服务")
    print()
    
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    start_backend()


if __name__ == '__main__':
    main()
