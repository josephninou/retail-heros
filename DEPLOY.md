# 🚀 Déploiement Retail-Heros — Guide Complet

## Option 1: Render.com (Recommandé — Gratuit)

### Étape 1: Créer un repo GitHub
```bash
git init
git add .
git commit -m "Initial commit"
# Crée un repo sur GitHub, puis:
git remote add origin https://github.com/TON_USER/retail-heros.git
git push -u origin main
```

### Étape 2: Déployer sur Render
1. Va sur [render.com](https://render.com) → Crée un compte (gratuit)
2. Clique **"New +"** → **"Web Service"**
3. Connecte ton repo GitHub
4. Render détecte automatiquement le `Dockerfile`
5. Clique **"Create Web Service"**
6. Attends le build (~5-10 min la première fois)
7. Ton app est live sur `https://retail-heros-xxx.onrender.com`

> ⚠️ Le free tier s'endort après 15 min d'inactivité. La première requête après le réveil prend ~1 min.

---

## Option 2: Railway.app (Gratuit avec $5 de crédit)

### Étape 1: CLI Railway
```bash
npm install -g @railway/cli
railway login
```

### Étape 2: Déployer
```bash
cd retail-heros
railway init
railway up
```

Ou via GitHub:
1. Va sur [railway.app](https://railway.app)
2. **"New Project"** → **"Deploy from GitHub repo"**
3. Sélectionne ton repo
4. Railway détecte le `railway.json`
5. Déploiement automatique à chaque push

---

## Option 3: Hugging Face Spaces (Gratuit — pour démos ML)

### Étape 1: Créer un Space
1. Va sur [huggingface.co/spaces](https://huggingface.co/spaces)
2. **"Create new Space"**
3. Nom: `retail-heros`
4. SDK: **Docker**
5. Visibility: **Public** (ou Private)

### Étape 2: Push le code
```bash
git clone https://huggingface.co/spaces/TON_USER/retail-heros
cd retail-heros
# Copie tous les fichiers du projet ici
git add .
git commit -m "Deploy Retail-Heros"
git push
```

> ⚠️ Hugging Face Spaces utilise le port 7860 (déjà configuré dans le Dockerfile).

---

## Option 4: VPS / Serveur dédié (DigitalOcean, Hetzner, OVH)

### Avec Docker
```bash
# Sur ton serveur
git clone https://github.com/TON_USER/retail-heros.git
cd retail-heros
docker build -t retail-heros .
docker run -d -p 8000:8000 --name retail-heros retail-heros
```

### Avec Docker Compose
```bash
docker-compose up -d
```

---

## 📱 Application Mobile (PWA)

Retail-Heros est déjà une **PWA** (Progressive Web App). Sur mobile :

### Android (Chrome)
1. Ouvre l'URL de ton app déployée
2. Menu (3 points) → **"Ajouter à l'écran d'accueil"**
3. L'app s'installe comme une vraie application native

### iOS (Safari)
1. Ouvre l'URL
2. Bouton Partager → **"Sur l'écran d'accueil"**
3. Nomme l'app "Retail-Heros"

### Fonctionnalités PWA
- ✅ Icône sur l'écran d'accueil
- ✅ Mode plein écran (sans barre d'adresse)
- ✅ Fonctionne hors ligne (cache des pages)
- ✅ Accès à la caméra pour prendre des photos
- ✅ Notifications (si activées)

---

## 🔧 Variables d'environnement

| Variable | Description | Défaut |
|----------|-------------|--------|
| `PORT` | Port du serveur | `8000` |
| `PYTHONUNBUFFERED` | Logs en temps réel | `1` |

---

## 📝 Récapitulatif des plateformes

| Plateforme | Prix | Facilité | Pour |
|-----------|------|----------|------|
| **Render** | Gratuit | ⭐⭐⭐⭐⭐ | Prototype, démo |
| **Railway** | $5 crédit | ⭐⭐⭐⭐⭐ | Prototype, test |
| **Hugging Face** | Gratuit | ⭐⭐⭐⭐ | Démo ML, communauté |
| **VPS** | ~$5/mois | ⭐⭐⭐ | Production, contrôle total |

---

**Retail-Heros** — *Déployé en 5 minutes, utilisé toute la vie.*
