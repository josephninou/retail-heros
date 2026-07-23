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

CATEGORIES = ["Boissons", "Snacks", "
