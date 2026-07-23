FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système (corrigé pour Debian 12)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Télécharger YOLOv8n (léger, 6MB)
RUN python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

# Copier le code
COPY main.py .

# Créer les dossiers nécessaires
RUN mkdir -p uploads

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
