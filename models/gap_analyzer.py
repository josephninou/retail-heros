import cv2
import numpy as np

class GapAnalyzer:
    def __init__(self):
        self.min_gap_area = 500
    
    def detect_gaps(self, image, detections):
        try:
            if not detections:
                return []
            
            height, width = image.shape[:2]
            occupied_mask = np.zeros((height, width), dtype=np.uint8)
            
            for det in detections:
                x1, y1, x2, y2 = map(int, det['bbox'])
                cv2.rectangle(occupied_mask, (x1, y1), (x2, y2), 255, -1)
            
            kernel = np.ones((20, 20), np.uint8)
            dilated_mask = cv2.dilate(occupied_mask, kernel, iterations=1)
            gap_mask = cv2.bitwise_not(dilated_mask)
            
            contours, _ = cv2.findContours(gap_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            gaps = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > self.min_gap_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    expected_product = self.estimate_missing_product(x, y, w, h, detections)
                    gaps.append({
                        'position': (x, y, w, h),
                        'area': area,
                        'expected_product': expected_product,
                        'severity': 'high' if area > 2000 else 'medium'
                    })
            
            return sorted(gaps, key=lambda g: g['area'], reverse=True)
            
        except Exception as e:
            print(f"❌ Erreur détection gaps: {str(e)}")
            return []
    
    def estimate_missing_product(self, x, y, w, h, detections):
        nearby_products = []
        for det in detections:
            dx, dy, dw, dh = det['bbox']
            center_x = x + w/2
            center_y = y + h/2
            det_center_x = dx + dw/2
            det_center_y = dy + dh/2
            
            distance = np.sqrt((center_x - det_center_x)**2 + (center_y - det_center_y)**2)
            if distance < 200:
                nearby_products.append(det['class'])
        
        if nearby_products:
            from collections import Counter
            most_common = Counter(nearby_products).most_common(1)
            return most_common[0][0] if most_common else "Inconnu"
        
        return "Inconnu"
