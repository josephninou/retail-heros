import cv2
import numpy as np
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
        try:
            print("🔄 Chargement de YOLOv8n...")
            self.model = YOLO('yolov8n.pt')
            self.model_loaded = True
            print("✅ Modèle YOLO chargé avec succès !")
        except Exception as e:
            print(f"❌ Erreur chargement YOLO: {str(e)}")
            self.model_loaded = False
    
    def load_products_db(self):
        try:
            possible_paths = [
                'data/products_db.json',
                '../data/products_db.json',
                './data/products_db.json'
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        return json.load(f)
            print("⚠️ Base produits non trouvée, utilisation du fallback")
            return {
                'bottle': {'category': 'Boissons', 'brand': 'Coca-Cola', 'price': 2.50, 'stock_min': 10},
                'wine glass': {'category': 'Boissons', 'brand': 'SOPEXA', 'price': 4.99, 'stock_min': 20},
                'cup': {'category': 'Boissons', 'brand': 'Tefal', 'price': 3.49, 'stock_min': 15},
                'chair': {'category': 'Mobilier', 'brand': 'IKEA', 'price': 89.99, 'stock_min': 5},
                'table': {'category': 'Mobilier', 'brand': 'IKEA', 'price': 149.99, 'stock_min': 3},
                'tv': {'category': 'Électronique', 'brand': 'Samsung', 'price': 599.99, 'stock_min': 3},
                'laptop': {'category': 'Électronique', 'brand': 'Dell', 'price': 899.99, 'stock_min': 2},
                'cell phone': {'category': 'Téléphonie', 'brand': 'Apple', 'price': 999.99, 'stock_min': 5},
                'book': {'category': 'Librairie', 'brand': 'Hachette', 'price': 24.99, 'stock_min': 30},
                'candy': {'category': 'Confiserie', 'brand': 'Haribo', 'price': 1.99, 'stock_min': 50},
                'snack': {'category': 'Alimentation', 'brand': "Lay's", 'price': 2.99, 'stock_min': 40}
            }
        except Exception as e:
            print(f"❌ Erreur chargement base produits: {str(e)}")
            return {}
    
    def analyze_shelf(self, image):
        if not self.model_loaded:
            return {'error': 'Modèle non chargé'}
        
        try:
            results = self.model(image, conf=0.25, verbose=False)
            
            detections = []
            categories = Counter()
            brands = Counter()
            
            for box in results[0].boxes:
                cls_id = int(box.cls[0])
                class_name = self.model.names[cls_id]
                confidence = float(box.conf[0])
                
                product_info = self.products_db.get(class_name, {})
                
                detections.append({
                    'class': class_name,
                    'confidence': confidence,
                    'bbox': box.xyxy[0].tolist(),
                    'category': product_info.get('category', 'Inconnu'),
                    'brand': product_info.get('brand', 'Inconnu'),
                    'price': product_info.get('price', 0),
                    'stock_min': product_info.get('stock_min', 5)
                })
                
                categories[product_info.get('category', 'Inconnu')] += 1
                brands[product_info.get('brand', 'Inconnu')] += 1
            
            total = len(detections)
            unique_products = len(set([d['class'] for d in detections]))
            
            expected_products = len(self.products_db)
            fill_rate = (unique_products / expected_products) * 100 if expected_products > 0 else 0
            
            planogram_compliance = min(100, fill_rate * 0.85)
            
            annotated_img = results[0].plot()
            
            return {
                'detections': detections,
                'total_products': total,
                'unique_products': unique_products,
                'categories': dict(categories),
                'brands': dict(brands),
                'fill_rate': round(fill_rate, 2),
                'planogram_compliance': round(planogram_compliance, 2),
                'annotated_image': annotated_img,
                'estimated_value': sum(d['price'] for d in detections),
                'stock_status': self.analyze_stock_status(detections)
            }
            
        except Exception as e:
            print(f"❌ Erreur analyse: {str(e)}")
            return {'error': str(e)}
    
    def analyze_stock_status(self, detections):
        stock_status = {}
        for det in detections:
            product = det['class']
            if product not in stock_status:
                stock_status[product] = {
                    'count': 0,
                    'min_required': det.get('stock_min', 5)
                }
            stock_status[product]['count'] += 1
        
        for product, data in stock_status.items():
            data['status'] = 'OK' if data['count'] >= data['min_required'] else 'Rupture'
        
        return stock_status
