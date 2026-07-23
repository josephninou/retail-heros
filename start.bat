@echo off
REM Retail-Heros — Script de lancement Windows

echo 🛒 Retail-Heros — Demarrage...
echo.

REM Verifier Python
python --version >nul 2>&1 || (echo ❌ Python non trouve & exit /b 1)

REM Creer venv si inexistant
if not exist "venv" (
    echo 📦 Creation de l'environnement virtuel...
    python -m venv venv
)

REM Activer venv
call venv\Scripts\activate.bat

REM Installer dependances
echo 📥 Installation des dependances...
pip install -q -r requirements.txt

echo.
echo ✅ Pret ! Ouvre http://localhost:8000 dans ton navigateur
echo.
python main.py
