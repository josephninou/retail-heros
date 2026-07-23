# Retail-Heros

Application open-source d'analyse de lineaire pour supermarches.

## Deploiement sur Render.com

1. Push ce repo sur GitHub
2. Sur Render : New + -> Web Service -> Connecte ton repo
3. Render detecte automatiquement le Dockerfile
4. Clique "Create Web Service"

## Structure

```
retail-heros/
├── main.py          # Backend FastAPI + Frontend SPA integre
├── Dockerfile       # Container Docker
├── requirements.txt # Dependances Python
└── render.yaml      # Config Render
```

## Fonctionnalites

- Upload d'image de rayon
- Detection produits (YOLOv8n)
- Lecture prix (EasyOCR)
- Identification marques
- Part de marche & facings
- Export CSV/JSON
