"""
Retail-Heros — Backend FastAPI
Analyse de lineaire supermarche avec YOLOv8 + EasyOCR
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import io
import json
import random
import re
from datetime import datetime
from typing import List, Dict, Any
from PIL import Image
import numpy as np

print("=" * 60)
print("[STARTUP] Retail-Heros demarrage...")
print("=" * 60)

# Configuration
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

BRANDS = [
    "Coca-Cola", "Pepsi", "Nestle", "Danone", "Unilever", "Procter & Gamble",
    "L'Oreal", "Mondelez", "Kellogg's", "Kraft Heinz", "Mars", "Ferrero",
    "Red Bull", "Nescafe", "Lipton", "Evian", "Volvic", "Cristaline",
    "Lay's", "Doritos", "Pringles", "Oreo", "Nutella", "Kinder",
    "Milka", "Lindt", "Haribo", "M&M's", "Snickers", "Twix",
    "Pampers", "Always", "Tampax", "Gillette", "Oral-B", "Dove",
    "Axe", "Rexona", "Nivea", "Garnier", "Head & Shoulders", "Pantene",
    "Colgate", "Signal", "Palmolive", "Ajax", "Mr. Propre", "Swiffer",
    "Levissime", "Systeme U", "Carrefour", "Auchan", "Casino", "Franprix",
    "Monoprix", "Leader Price", "Intermarche", "E.Leclerc", "Lidl", "Aldi"
]

CATEGORIES = ["Boissons", "Snacks", "Produits laitiers", "Entretien", "Hygiene", "Epicerie"]

app = FastAPI(title="Retail-Heros", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chargement des modeles IA AU DEMARRAGE
_yolo_model = None
_ocr_reader = None
_yolo_available = False
_ocr_available = False

try:
    print("[INIT] Chargement YOLOv8n...")
    from ultralytics import YOLO
    _yolo_model = YOLO("yolov8n.pt")
    _yolo_available = True
    print("[INIT] YOLOv8n CHARGE!")
except Exception as e:
    print(f"[INIT] ERREUR YOLO: {e}")
    _yolo_available = False

try:
    print("[INIT] Chargement EasyOCR...")
    import easyocr
    _ocr_reader = easyocr.Reader(['fr', 'en'], gpu=False, verbose=False)
    _ocr_available = True
    print("[INIT] EasyOCR CHARGE!")
except Exception as e:
    print(f"[INIT] ERREUR OCR: {e}")
    _ocr_available = False

print(f"[INIT] STATUT FINAL — YOLO: {_yolo_available}, OCR: {_ocr_available}")
print("=" * 60)

def analyze_image(image_bytes: bytes) -> Dict[str, Any]:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img_array = np.array(image)
    
    results = {
        "products": [], "prices": [], "brands": {}, "facings": {},
        "total_products": 0, "total_facings": 0, "avg_price": 0.0,
        "market_share": {}, "timestamp": datetime.now().isoformat(),
        "image_width": image.width, "image_height": image.height,
        "yolo_available": _yolo_available, "ocr_available": _ocr_available,
        "simulated": False,
    }
    
    detections = []
    if _yolo_available and _yolo_model is not None:
        try:
            print("[ANALYSE] YOLO detection...")
            yolo_results = _yolo_model(img_array, verbose=False)
            for r in yolo_results:
                for box in r.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    label = _yolo_model.names.get(cls, f"objet_{cls}")
                    detections.append({"bbox": [x1, y1, x2, y2], "confidence": round(conf, 3), "label": label})
            print(f"[ANALYSE] YOLO: {len(detections)} detections")
        except Exception as e:
            print(f"[ANALYSE] YOLO erreur: {e}")
    
    if not detections:
        detections = simulate_detections(image.width, image.height)
        results["simulated"] = True
        print(f"[ANALYSE] Simulation: {len(detections)} objets")
    
    prices = []
    if _ocr_available and _ocr_reader is not None:
        try:
            print("[ANALYSE] OCR lecture...")
            ocr_results
