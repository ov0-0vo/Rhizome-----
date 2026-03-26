@echo off
chcp 65001 >nul
title Rhizome - 打包工具

echo ================================================
echo   Rhizome Windows 安装包打包工具
echo ================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Node.js
    pause
    exit /b 1
)

echo [步骤 1/5] 安装 Python 依赖...
pip install pyinstaller -q
pip install -e . -q

echo [步骤 2/5] 构建前端...
cd frontend
call npm install --silent
call npm run build
cd ..

echo [步骤 3/5] 使用 PyInstaller 打包...
pyinstaller rhizome.spec --clean -y

echo [步骤 4/5] 复制数据文件...
if not exist "dist\Rhizome\data" mkdir "dist\Rhizome\data"
xcopy /E /I /Y "data" "dist\Rhizome\data"

if exist ".env.example" copy /Y ".env.example" "dist\Rhizome\"

echo [步骤 5/5] 创建启动脚本...
(
echo @echo off
echo chcp 65001 ^>nul
echo title Rhizome
echo cd /d "%%~dp0"
echo if not exist ".env" (
echo     if exist ".env.example" copy .env.example .env
echo     echo 请先编辑 .env 文件配置 API 密钥
echo     notepad .env
echo )
echo start "" http://localhost:8000
echo Rhizome.exe
) > "dist\Rhizome\启动.bat"

echo.
echo ================================================
echo   打包完成！
echo   输出目录: dist\Rhizome
echo ================================================
echo.
echo 使用方法:
echo 1. 进入 dist\Rhizome 目录
echo 2. 编辑 .env 文件配置 API 密钥
echo 3. 双击 启动.bat 或 Rhizome.exe 运行程序
echo.

pause
