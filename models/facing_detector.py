import numpy as np
from collections import defaultdict

class FacingDetector:
    def __init__(self):
        self.min_facing_width = 10
    
    def count_facings(self, detections, image_width):
        try:
            products_by_class = defaultdict(list)
            for det in detections:
                products_by_class[det['class']].append(det)
            
            product_facings = defaultdict(int)
            
            for product_name, product_dets in products_by_class.items():
                facings_count = 0
                for det in product_dets:
                    x1, y1, x2, y2 = det['bbox']
                    facing_width = x2 - x1
                    
                    if facing_width >= self.min_facing_width:
                        count = int(facing_width / self.min_facing_width)
                        facings_count += max(1, count)
                    else:
                        facings_count += 1
                
                product_facings[product_name] = facings_count
            
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
