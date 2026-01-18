@echo off
REM Omni-Help Backend Setup Script for Windows

echo 🚀 Setting up Omni-Help Backend...

REM Create virtual environment
echo 📦 Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo 🔌 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📥 Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

REM Create necessary directories
echo 📁 Creating directories...
if not exist data mkdir data
if not exist logs mkdir logs

REM Copy environment file
if not exist .env (
    echo ⚙️  Creating .env file...
    copy .env.example .env
    echo ⚠️  Please edit .env and add your OPENAI_API_KEY
) else (
    echo ✅ .env file already exists
)

echo.
echo ✅ Setup complete!
echo.
echo Next steps:
echo 1. Edit .env and add your OPENAI_API_KEY
echo 2. Activate virtual environment: venv\Scripts\activate
echo 3. Run the server: python main.py
echo.

pause

