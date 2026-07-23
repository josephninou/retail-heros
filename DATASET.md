# 🏋️ Dataset & Entraînement — Retail-Heros

Guide complet pour entraîner ton propre modèle YOLO sur des rayons de supermarché.

---

## 📦 Datasets Publics Disponibles

### 1. SKU110K (Recommandé) ⭐
- **Images**: 11,743 photos de rayons du monde entier
- **Annotations**: 1.7M+ bounding boxes
- **Format**: CSV (converti automatiquement en YOLO)
- **Taille**: ~13.6 GB
- **Licence**: Publique (académique)
- **Citation**: Goldman et al., CVPR 2019

**Téléchargement rapide** (YOLO le fait automatiquement) :
```python
from ultralytics import YOLO
model = YOLO("yolov8n.pt")
model.train(data="SKU110K.yaml", epochs=100, imgsz=640)
# YOLO télécharge et convertit tout seul !
```

**Liens**:
- GitHub: https://github.com/eg4000/SKU110K_CVPR19
- Kaggle: https://www.kaggle.com/datasets/thedatasith/sku110k-annotations
- HuggingFace: https://huggingface.co/datasets/PrashantDixit0/SKU-110K
- Docs Ultralytics: https://docs.ultralytics.com/datasets/detect/sku-110k

---

### 2. Roboflow Universe — Supermarket Shelves
- **Images**: 150+ images annotées
- **Format**: YOLO (prêt à l'emploi)
- **Modèle pré-entraîné**: ✅ Oui
- **Licence**: CC BY 4.0

**Lien**: https://universe.roboflow.com/cosc428-zld36/supermarket-shelves-7eum5

---

### 3. Roboflow — Retail Shelf Detection
- **Images**: 269 images
- **Format**: YOLO
- **Focus**: Détection d'étagères

**Lien**: https://universe.roboflow.com/ragupathy/retail-shelf-detection

---

### 4. Roboflow — Retail Shelf Availability
- **Images**: 4,588 images
- **Format**: YOLO
- **Focus**: Disponibilité des produits (OOS)

**Lien**: https://universe.roboflow.com/srm-university-52jqz/retail-shelf-availability

---

### 5. Grocery Dataset
- **Images**: 680 images
- **Catégories**: 80 marques de produits
- **Format**: TXT custom
- **Licence**: Académique

**Lien**: https://github.com/gulvarol/grocerydataset

---

## 🚀 Entraînement Rapide (3 lignes)

```python
from ultralytics import YOLO

# 1. Charger le modèle pré-entraîné
model = YOLO("yolov8n.pt")

# 2. Entraîner sur SKU110K (téléchargement auto)
results = model.train(data="SKU110K.yaml", epochs=100, imgsz=640)

# 3. Le modèle est sauvegardé dans runs/detect/train/weights/best.pt
```

---

## 🎯 Entraînement Avancé

```python
from ultralytics import YOLO

model = YOLO("yolov8n.pt")

# Configuration optimisée pour Retail-Heros
results = model.train(
    data="SKU110K.yaml",           # Dataset
    epochs=100,                     # Nombre d'epochs
    imgsz=640,                      # Taille des images
    batch=16,                       # Batch size
    name="retail-heros",            # Nom de l'expérience
    patience=20,                    # Early stopping

    # Augmentation de données
    hsv_h=0.015,                    # Variation teinte
    hsv_s=0.7,                      # Variation saturation
    hsv_v=0.4,                      # Variation luminosité
    translate=0.1,                  # Translation
    scale=0.5,                      # Scaling
    fliplr=0.5,                     # Flip horizontal
    mosaic=1.0,                     # Mosaic augmentation

    # Optimiseur
    optimizer="AdamW",
    lr0=0.001,
    lrf=0.01,

    # Sauvegarde
    save=True,
    save_period=10
)
```

---

## 📸 Créer ton Propre Dataset

### Étape 1: Collecte (30 min)
- Prends 200-500 photos de tes rayons
- Variété: angles, distances, éclairages
- Format: JPG, minimum 1920x1080

### Étape 2: Annotation avec Roboflow (Gratuit)
1. Va sur https://universe.roboflow.com
2. Crée un projet → "retail-heros"
3. Upload tes images
4. **Dessine une bounding box autour de CHAQUE produit**
5. Classe unique: "product"
6. Exporte en **YOLOv8 format**
7. Dézippe dans `dataset/custom/`

### Étape 3: Entraîner
```bash
python prepare_dataset.py --train --dataset custom --epochs 100
```

---

## 📊 Résultats Attendus

| Modèle | mAP@0.5 | Vitesse | Taille | Usage |
|--------|---------|---------|--------|-------|
| yolov8n | ~0.65 | Très rapide | 6.2 MB | Mobile, edge |
| yolov8s | ~0.72 | Rapide | 21.5 MB | Production |
| yolov8m | ~0.78 | Moyen | 49.7 MB | Serveur |
| yolov8l | ~0.82 | Lent | 83.7 MB | Haute précision |

---

## 🔗 Liens Utiles

| Ressource | Lien |
|-----------|------|
| SKU110K GitHub | https://github.com/eg4000/SKU110K_CVPR19 |
| SKU110K Kaggle | https://www.kaggle.com/datasets/thedatasith/sku110k-annotations |
| SKU110K HuggingFace | https://huggingface.co/datasets/PrashantDixit0/SKU-110K |
| Roboflow Supermarket | https://universe.roboflow.com/cosc428-zld36/supermarket-shelves-7eum5 |
| Roboflow Retail Detection | https://universe.roboflow.com/ragupathy/retail-shelf-detection |
| Roboflow Availability | https://universe.roboflow.com/srm-university-52jqz/retail-shelf-availability |
| Grocery Dataset | https://github.com/gulvarol/grocerydataset |
| Ultralytics Docs | https://docs.ultralytics.com/datasets/detect/sku-110k |
| LabelImg | https://github.com/tzutalin/labelImg |
| CVAT | https://cvat.org |

---

## 💡 Conseils Pro

1. **Commence par SKU110K** → c'est le meilleur dataset public
2. **Fine-tune** sur tes propres images pour + de précision
3. **Utilise yolov8n** pour mobile, **yolov8m** pour serveur
4. **Minimum 50 images** perso pour voir une amélioration
5. **200+ images** perso pour un résultat professionnel

---

**Retail-Heros** — *Entraîne, déploie, analyse.* 🦸
