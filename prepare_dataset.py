#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  RETAIL-HEROS — Générateur de Dataset YOLO pour rayons de supermarché     ║
║  Télécharge, convertit et prépare les données d'entraînement              ║
╚══════════════════════════════════════════════════════════════════════════════╝

USAGE:
    python prepare_dataset.py --source sku110k      # Télécharge SKU110K
    python prepare_dataset.py --source roboflow     # Télécharge datasets Roboflow
    python prepare_dataset.py --source custom       # Prépare ton propre dataset
    python prepare_dataset.py --train              # Lance l'entraînement

LIENS RAPIDES:
    SKU110K:        https://github.com/eg4000/SKU110K_CVPR19
    Roboflow:       https://universe.roboflow.com/search?q=retail%20shelf
    Kaggle:         https://www.kaggle.com/datasets/thedatasith/sku110k-annotations
    HuggingFace:    https://huggingface.co/datasets/PrashantDixit0/SKU-110K
"""

import os
import sys
import argparse
import shutil
import json
import csv
import tarfile
import zipfile
from pathlib import Path
from urllib.request import urlretrieve
from urllib.parse import urlparse
import numpy as np
from PIL import Image

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
BASE_DIR = Path(__file__).parent
DATASET_DIR = BASE_DIR / "dataset"
MODELS_DIR = BASE_DIR / "models"

# URLs des datasets publics
DATASETS = {
    "sku110k": {
        "name": "SKU110K",
        "description": "11,743 images de rayons densément peuplés, 1.7M+ bounding boxes",
        "size": "~13.6 GB",
        "url": "http://trax-geometry.s3.amazonaws.com/cvpr_challenge/SKU110K_fixed.tar.gz",
        "format": "custom_csv",  # Format CSV custom à convertir
        "license": "Public (academic)",
        "citation": "Goldman et al., CVPR 2019"
    },
    "grocery": {
        "name": "Grocery Dataset",
        "description": "680 images d'étagères avec 80 catégories de produits",
        "size": "~500 MB",
        "url": "https://github.com/gulvarol/grocerydataset",
        "format": "custom_txt",
        "license": "Academic",
        "citation": "Varol & Kuzu, ICIVC 2014"
    },
    "roboflow_shelves": {
        "name": "Roboflow - Supermarket Shelves",
        "description": "150 images annotées, modèle pré-entraîné disponible",
        "size": "~100 MB",
        "url": "https://universe.roboflow.com/cosc428-zld36/supermarket-shelves-7eum5",
        "format": "yolo",
        "license": "CC BY 4.0",
        "citation": "COSC428"
    },
    "roboflow_retail": {
        "name": "Roboflow - Retail Shelf Detection",
        "description": "269 images de détection d'étagères",
        "size": "~150 MB",
        "url": "https://universe.roboflow.com/ragupathy/retail-shelf-detection",
        "format": "yolo",
        "license": "Open Source",
        "citation": "Ragupathy"
    },
    "roboflow_availability": {
        "name": "Roboflow - Retail Shelf Availability",
        "description": "4,588 images de disponibilité en rayon",
        "size": "~800 MB",
        "url": "https://universe.roboflow.com/srm-university-52jqz/retail-shelf-availability",
        "format": "yolo",
        "license": "Open Source",
        "citation": "SRM University"
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════════

def print_header(text):
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")

def print_dataset_info():
    """Affiche les datasets disponibles."""
    print_header("DATASETS DISPONIBLES")
    for key, ds in DATASETS.items():
        print(f"  📦 {key}")
        print(f"     Nom:        {ds['name']}")
        print(f"     Description: {ds['description']}")
        print(f"     Taille:     {ds['size']}")
        print(f"     Format:     {ds['format']}")
        print(f"     Licence:    {ds['license']}")
        print(f"     URL:        {ds['url']}")
        print(f"     Citation:   {ds['citation']}")
        print()

def create_yolo_structure(base_path: Path):
    """Crée la structure de dossiers YOLO."""
    dirs = ["images/train", "images/val", "images/test", "labels/train", "labels/val", "labels/test"]
    for d in dirs:
        (base_path / d).mkdir(parents=True, exist_ok=True)
    print(f"✅ Structure YOLO créée dans {base_path}")

def download_file(url: str, dest: Path, desc: str = "Téléchargement"):
    """Télécharge un fichier avec barre de progression."""
    print(f"📥 {desc}...")
    print(f"   URL: {url}")
    print(f"   Dest: {dest}")

    def progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        percent = min(100, downloaded * 100 / total_size) if total_size > 0 else 0
        bar = "█" * int(percent / 2) + "░" * (50 - int(percent / 2))
        print(f"\r   [{bar}] {percent:.1f}%", end="", flush=True)

    try:
        urlretrieve(url, dest, reporthook=progress)
        print(f"\n✅ Téléchargement terminé: {dest.stat().st_size / (1024**2):.1f} MB")
        return True
    except Exception as e:
        print(f"\n❌ Erreur téléchargement: {e}")
        return False

# ═══════════════════════════════════════════════════════════════════════════════
# CONVERTISSEURS DE FORMAT
# ═══════════════════════════════════════════════════════════════════════════════

def convert_sku110k_to_yolo(sku_dir: Path, output_dir: Path):
    """
    Convertit le dataset SKU110K (format CSV) en format YOLO.

    Format SKU110K CSV:
        image_name, x1, y1, x2, y2, class, image_width, image_height

    Format YOLO:
        class x_center y_center width height (normalisé 0-1)
    """
    print_header("CONVERSION SKU110K → YOLO")

    annotations_dir = sku_dir / "annotations"
    images_dir = sku_dir / "images"

    if not annotations_dir.exists():
        print(f"❌ Dossier annotations non trouvé: {annotations_dir}")
        print("   Assure-toi d'avoir extrait l'archive SKU110K.")
        return False

    create_yolo_structure(output_dir)

    splits = {
        "train": ("annotations_train.csv", "train"),
        "val": ("annotations_val.csv", "val"),
        "test": ("annotations_test.csv", "test")
    }

    for split_name, (csv_file, yolo_split) in splits.items():
        csv_path = annotations_dir / csv_file
        if not csv_path.exists():
            print(f"⚠️  Fichier {csv_file} non trouvé, skip {split_name}")
            continue

        print(f"\n🔄 Conversion {split_name}...")

        # Lire le CSV
        with open(csv_path, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)

        # Regrouper les annotations par image
        images_data = {}
        for row in rows:
            if len(row) < 8:
                continue
            img_name = row[0]
            x1, y1, x2, y2 = map(float, row[1:5])
            img_w, img_h = float(row[6]), float(row[7])

            if img_name not in images_data:
                images_data[img_name] = []

            # Convertir en YOLO format (normalisé)
            x_center = ((x1 + x2) / 2) / img_w
            y_center = ((y1 + y2) / 2) / img_h
            width = (x2 - x1) / img_w
            height = (y2 - y1) / img_h

            # Classe 0 = produit (SKU110K est single-class)
            images_data[img_name].append(f"0 {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")

        # Écrire les fichiers
        converted = 0
        for img_name, labels in images_data.items():
            # Copier l'image
            src_img = images_dir / split_name / img_name
            if not src_img.exists():
                # Essayer sans sous-dossier
                src_img = images_dir / img_name

            if src_img.exists():
                dst_img = output_dir / f"images/{yolo_split}" / img_name
                shutil.copy2(src_img, dst_img)

            # Écrire le label
            label_file = output_dir / f"labels/{yolo_split}" / Path(img_name).with_suffix(".txt")
            with open(label_file, 'w') as f:
                f.write("\n".join(labels) + "\n")
            converted += 1

        print(f"   ✅ {converted} images converties pour {split_name}")

    return True

def convert_roboflow_to_yolo(roboflow_dir: Path, output_dir: Path):
    """
    Convertit un dataset Roboflow (déjà en format YOLO) en structure standard.
    Roboflow exporte généralement: train/, valid/, test/ avec images/ et labels/
    """
    print_header("CONVERSION ROBOFLOW → YOLO STANDARD")

    create_yolo_structure(output_dir)

    # Mapping des dossiers Roboflow → YOLO
    mappings = {
        "train": "train",
        "valid": "val",
        "test": "test"
    }

    for roboflow_split, yolo_split in mappings.items():
        src_img_dir = roboflow_dir / roboflow_split / "images"
        src_lbl_dir = roboflow_dir / roboflow_split / "labels"

        if not src_img_dir.exists():
            print(f"⚠️  Dossier {roboflow_split} non trouvé, skip")
            continue

        print(f"\n🔄 Copie {roboflow_split} → {yolo_split}...")

        # Copier images
        dst_img_dir = output_dir / f"images/{yolo_split}"
        for img in src_img_dir.glob("*"):
            shutil.copy2(img, dst_img_dir / img.name)

        # Copier labels
        dst_lbl_dir = output_dir / f"labels/{yolo_split}"
        for lbl in src_lbl_dir.glob("*.txt"):
            shutil.copy2(lbl, dst_lbl_dir / lbl.name)

        img_count = len(list(dst_img_dir.glob("*")))
        lbl_count = len(list(dst_lbl_dir.glob("*.txt")))
        print(f"   ✅ {img_count} images, {lbl_count} labels")

    return True

def create_data_yaml(dataset_dir: Path, class_names: list = None):
    """Crée le fichier data.yaml pour YOLOv8."""
    if class_names is None:
        class_names = ["product"]  # SKU110K est single-class

    yaml_content = f"""# Retail-Heros Dataset Configuration
# Généré automatiquement par prepare_dataset.py

path: {dataset_dir.absolute()}  # chemin racine du dataset
train: images/train
val: images/val
test: images/test

# Classes
nc: {len(class_names)}  # nombre de classes
names: {class_names}

# Retail-Heros — Analyse de linéaire par IA
"""

    yaml_path = dataset_dir / "data.yaml"
    with open(yaml_path, 'w') as f:
        f.write(yaml_content)

    print(f"\n✅ Fichier data.yaml créé: {yaml_path}")
    return yaml_path

# ═══════════════════════════════════════════════════════════════════════════════
# PRÉPARATION DATASET PERSONNALISÉ
# ═══════════════════════════════════════════════════════════════════════════════

def setup_custom_dataset():
    """
    Guide l'utilisateur pour créer son propre dataset.
    """
    print_header("CRÉATION D'UN DATASET PERSONNALISÉ")

    print("""
📸 ÉTAPE 1: COLLECTE D'IMAGES
   → Prends 200-500 photos de tes rayons (différents angles, éclairages)
   → Format recommandé: JPG, 1920x1080 minimum
   → Place les images dans: dataset/custom/images/

✏️  ÉTAPE 2: ANNOTATION (choisis un outil)

   Option A — Roboflow (Recommandé, Gratuit):
   1. Va sur https://universe.roboflow.com
   2. Crée un projet "retail-heros"
   3. Upload tes images
   4. Dessine des bounding boxes autour de CHAQUE produit
   5. Exporte en format YOLOv8
   6. Dézippe dans dataset/custom/

   Option B — LabelImg (Offline):
   1. pip install labelImg
   2. labelImg dataset/custom/images/ dataset/custom/labels/
   3. Format: YOLO (PAS PascalVOC)
   4. Crée un fichier classes.txt avec: product

   Option C — CVAT (Collaboratif):
   1. Va sur https://cvat.org
   2. Crée un projet, upload les images
   3. Annoter avec bounding boxes
   4. Exporte en YOLO

🏋️ ÉTAPE 3: STRUCTURE ATTENDUE
   dataset/custom/
   ├── images/
   │   ├── train/     ← 80% des images
   │   ├── val/       ← 10% des images
   │   └── test/      ← 10% des images
   ├── labels/
   │   ├── train/     ← Fichiers .txt YOLO
   │   ├── val/
   │   └── test/
   └── data.yaml      ← Sera généré automatiquement

💡 CONSEILS:
   • Plus les images sont variées (angles, distances, éclairages), mieux c'est
   • Chaque produit doit avoir sa propre bounding box
   • Évite les images floues ou trop sombres
   • ~50 images minimum pour un résultat acceptable
   • ~200+ images pour un résultat professionnel
""")

    custom_dir = DATASET_DIR / "custom"
    create_yolo_structure(custom_dir)

    print(f"\n✅ Dossier créé: {custom_dir}")
    print("   Place tes images et labels ici, puis lance:")
    print("   python prepare_dataset.py --train --dataset custom")

# ═══════════════════════════════════════════════════════════════════════════════
# ENTRAÎNEMENT YOLO
# ═══════════════════════════════════════════════════════════════════════════════

def train_yolo(dataset_name: str = "sku110k", epochs: int = 100, imgsz: int = 640, model: str = "yolov8n"):
    """
    Lance l'entraînement YOLOv8 sur le dataset préparé.
    """
    print_header(f"ENTRAÎNEMENT YOLOv8 — Dataset: {dataset_name}")

    try:
        from ultralytics import YOLO
    except ImportError:
        print("❌ Ultralytics non installé. Lance:")
        print("   pip install ultralytics")
        return False

    dataset_dir = DATASET_DIR / dataset_name
    data_yaml = dataset_dir / "data.yaml"

    if not data_yaml.exists():
        print(f"❌ Fichier data.yaml non trouvé: {data_yaml}")
        print("   Lance d'abord: python prepare_dataset.py --source [nom]")
        return False

    print(f"📊 Configuration:")
    print(f"   Dataset:    {dataset_dir}")
    print(f"   Modèle:     {model}.pt")
    print(f"   Epochs:     {epochs}")
    print(f"   Image size: {imgsz}")
    print(f"   Output:     {BASE_DIR / 'runs/detect/retail-heros'}")
    print()

    # Charger le modèle pré-entraîné
    print("🔄 Chargement du modèle...")
    yolo_model = YOLO(f"{model}.pt")

    # Lancer l'entraînement
    print("🏋️  Lancement de l'entraînement...")
    print("   (Cela peut prendre plusieurs heures selon ton GPU)")
    print()

    results = yolo_model.train(
        data=str(data_yaml),
        epochs=epochs,
        imgsz=imgsz,
        batch=16,
        name="retail-heros",
        project=str(BASE_DIR / "runs/detect"),
        patience=20,  # Early stopping
        save=True,
        pretrained=True,
        optimizer="AdamW",
        lr0=0.001,
        lrf=0.01,
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=3.0,
        box=7.5,
        cls=0.5,
        dfl=1.5,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=0.0,
        translate=0.1,
        scale=0.5,
        shear=0.0,
        perspective=0.0,
        flipud=0.0,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.0,
        copy_paste=0.0,
        auto_augment="randaugment",
        erasing=0.4,
        crop_fraction=1.0
    )

    # Copier le meilleur modèle
    best_model = BASE_DIR / "runs/detect/retail-heros/weights/best.pt"
    if best_model.exists():
        target = MODELS_DIR / "retail-heros-yolo.pt"
        MODELS_DIR.mkdir(exist_ok=True)
        shutil.copy2(best_model, target)
        print(f"\n✅ Modèle entraîné sauvegardé: {target}")
        print("   Retail-Heros utilisera automatiquement ce modèle !")

    return True

def validate_model():
    """Valide le modèle entraîné sur le jeu de test."""
    print_header("VALIDATION DU MODÈLE")

    try:
        from ultralytics import YOLO
    except ImportError:
        print("❌ Ultralytics non installé")
        return

    model_path = MODELS_DIR / "retail-heros-yolo.pt"
    if not model_path.exists():
        print(f"❌ Modèle non trouvé: {model_path}")
        print("   Lance d'abord l'entraînement")
        return

    print("🔄 Chargement du modèle...")
    model = YOLO(str(model_path))

    print("📊 Validation sur le jeu de test...")
    results = model.val()

    print(f"\n📈 Résultats:")
    print(f"   mAP@0.5:    {results.box.map50:.4f}")
    print(f"   mAP@0.5:0.95: {results.box.map:.4f}")
    print(f"   Precision:  {results.box.mp:.4f}")
    print(f"   Recall:     {results.box.mr:.4f}")

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Retail-Heros — Préparation de dataset YOLO",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python prepare_dataset.py --info                    # Liste les datasets
  python prepare_dataset.py --source sku110k           # Télécharge SKU110K
  python prepare_dataset.py --source roboflow_shelves  # Dataset Roboflow
  python prepare_dataset.py --custom                   # Guide dataset perso
  python prepare_dataset.py --train --dataset sku110k  # Entraîne YOLO
  python prepare_dataset.py --validate                 # Valide le modèle
        """
    )

    parser.add_argument("--info", action="store_true", help="Affiche les datasets disponibles")
    parser.add_argument("--source", choices=list(DATASETS.keys()) + ["custom"], 
                        help="Source du dataset à télécharger")
    parser.add_argument("--custom", action="store_true", help="Guide pour dataset personnalisé")
    parser.add_argument("--train", action="store_true", help="Lance l'entraînement YOLO")
    parser.add_argument("--dataset", default="sku110k", help="Nom du dataset pour l'entraînement")
    parser.add_argument("--epochs", type=int, default=100, help="Nombre d'epochs (défaut: 100)")
    parser.add_argument("--imgsz", type=int, default=640, help="Taille des images (défaut: 640)")
    parser.add_argument("--model", default="yolov8n", 
                        choices=["yolov8n", "yolov8s", "yolov8m", "yolov8l", "yolov8x"],
                        help="Variante YOLOv8 (défaut: yolov8n)")
    parser.add_argument("--validate", action="store_true", help="Valide le modèle entraîné")

    args = parser.parse_args()

    if args.info or len(sys.argv) == 1:
        print_dataset_info()
        print("\n💡 Utilise --source [nom] pour télécharger un dataset")
        print("   ou --custom pour créer ton propre dataset")
        return

    if args.custom:
        setup_custom_dataset()
        return

    if args.source:
        if args.source == "custom":
            setup_custom_dataset()
            return

        ds_info = DATASETS.get(args.source)
        if not ds_info:
            print(f"❌ Dataset inconnu: {args.source}")
            return

        print_header(f"TÉLÉCHARGEMENT: {ds_info['name']}")
        print(f"Description: {ds_info['description']}")
        print(f"Taille: {ds_info['size']}")
        print(f"URL: {ds_info['url']}")
        print()
        print("⚠️  Pour les datasets lourds, téléchargement manuel recommandé:")
        print(f"   1. Va sur {ds_info['url']}")
        print(f"   2. Télécharge le dataset")
        print(f"   3. Place-le dans: {DATASET_DIR / args.source}")
        print(f"   4. Lance: python prepare_dataset.py --train --dataset {args.source}")
        print()
        print("📝 Alternative rapide avec SKU110K:")
        print("   from ultralytics import YOLO")
        print("   model = YOLO('yolov8n.pt')")
        print("   model.train(data='SKU110K.yaml', epochs=100, imgsz=640)")
        print("   # YOLO télécharge automatiquement SKU110K !")
        return

    if args.train:
        train_yolo(args.dataset, args.epochs, args.imgsz, args.model)
        return

    if args.validate:
        validate_model()
        return

if __name__ == "__main__":
    main()
