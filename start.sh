#!/bin/bash
# Retail-Heros — Script de lancement rapide

echo "🛒 Retail-Heros — Demarrage..."
echo ""

# Verifier Python
python3 --version > /dev/null 2>&1 || { echo "❌ Python 3 non trouve"; exit 1; }

# Creer venv si inexistant
if [ ! -d "venv" ]; then
    echo "📦 Creation de l'environnement virtuel..."
    python3 -m venv venv
fi

# Activer venv
source venv/bin/activate

# Installer dependances
echo "📥 Installation des dependances..."
pip install -q -r requirements.txt

# Lancer
echo ""
echo "✅ Pret ! Ouvre http://localhost:8000 dans ton navigateur"
echo ""
python main.py
