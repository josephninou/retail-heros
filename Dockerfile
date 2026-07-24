FROM python:3.10-slim

WORKDIR /app

# Variables d'environnement pour optimiser la mémoire
ENV PYTHONUNBUFFERED=1
ENV PYTHONOPTIMIZE=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV ULTRALYTICS_MEMORY_LIMIT=256

# Installer les dépendances système CORRECTES
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copier et installer Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code
COPY . .

# Créer les dossiers nécessaires
RUN mkdir -p data models utils static

# Téléchargement du modèle au démarrage (pas pendant le build)
RUN echo "from ultralytics import YOLO; YOLO('yolov8n.pt')" > /tmp/download_model.py && \
    python /tmp/download_model.py || true && \
    rm /tmp/download_model.py

# Port Render
EXPOSE 10000

# Commande de démarrage
CMD ["python", "app.py"]
