import cv2
import numpy as np
import torch
from ultralytics import YOLO
import json
import os
from collections import Counter

class ProductDetector:
    def __init__(self):
        self.model = None
        self.products_db = self.load_products_db()
        self.model_loaded = False
        self.load_model()
    
    def load_model(self):
        """Charge le modèle YOLO en patchant PyTorch"""
        try:
            print("🔄 Chargement de YOLOv8n...")
            # Patcher PyTorch pour autoriser le chargement
            from ultralytics.nn.tasks import DetectionModel
            torch.serialization.add_safe_globals([DetectionModel])
            self.model = YOLO('yolov8n.pt')
            self.model_loaded = True
            print("✅ Modèle YOLO chargé avec succès !")
        except Exception as e:
            print(f"❌ Erreur chargement YOLO: {str(e)}")
            self.model_loaded = False
    
    # ... (le reste du fichier est identique)
