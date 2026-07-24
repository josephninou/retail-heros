import numpy as np
from collections import defaultdict

class FacingDetector:
    def __init__(self):
        self.min_facing_width = 10  # pixels, ajustable
    
    def count_facings(self, detections, image_width):
        """
        Compte les facings et calcule le Share of Shelf
        """
        try:
            # Grouper les produits par classe
            products_by_class = defaultdict(list)
            for det in detections:
                products_by_class[det['class']].append(det)
            
            product_facings = defaultdict(int)
            
            for product_name, product_dets in products_by_class.items():
                # Compter les facings en analysant la largeur des bbox
                facings_count = 0
                for det in product_dets:
                    x1, y1, x2, y2 = det['bbox']
                    facing_width = x2 - x1
                    
                    # Si la largeur est suffisante, c'est un facing
                    if facing_width >= self.min_facing_width:
                        # Un produit large peut représenter plusieurs facings
                        count = int(facing_width / self.min_facing_width)
                        facings_count += max(1, count)
                    else:
                        # Petit produit = 1 facing
                        facings_count += 1
                
                product_facings[product_name] = facings_count
            
            # Calcul du Share of Shelf
            total_facings = sum(product_facings.values())
            share_of_shelf = {}
            if total_facings > 0:
                for product, count in product_facings.items():
                    share_of_shelf[product] = (count / total_facings) * 100
            
            return {
                'product_facings': dict(product_facings),
                'total_facings': total_facings,
                'share_of_shelf': share_of_shelf,
                'average_facing_width': self.min_facing_width
            }
            
        except Exception as e:
            print(f"❌ Erreur analyse facings: {str(e)}")
            return {
                'product_facings': {},
                'total_facings': 0,
                'share_of_shelf': {},
                'error': str(e)
            }
    
    def analyze_shelf_position(self, detections):
        """
        Analyse la position des produits sur le rayon
        """
        positions = {
            'top': [],
            'middle': [],
            'bottom': []
        }
        
        # Déterminer les zones du rayon
        if detections:
            y_coords = []
            for det in detections:
                _, y1, _, y2 = det['bbox']
                y_coords.extend([y1, y2])
            
            if y_coords:
                min_y = min(y_coords)
                max_y = max(y_coords)
                height = max_y - min_y
                
                for det in detections:
                    _, y1, _, y2 = det['bbox']
                    center_y = (y1 + y2) / 2
                    relative_pos = (center_y - min_y) / height if height > 0 else 0.5
                    
                    if relative_pos < 0.33:
                        positions['top'].append(det['class'])
                    elif relative_pos < 0.66:
                        positions['middle'].append(det['class'])
                    else:
                        positions['bottom'].append(det['class'])
        
        return positions
