import gradio as gr
import os
import json
import hashlib
import secrets
from datetime import datetime
import cv2
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import gc
import torch

# ===== OPTIMISATIONS MÉMOIRE (IMPORTANT POUR RENDER) =====
os.environ['YOLO_VERBOSE'] = 'False'
os.environ['ULTRALYTICS_MEMORY_LIMIT'] = '256'
if torch.cuda.is_available():
    torch.cuda.empty_cache()

# ===== IMPORTS DES MODULES RETAIL =====
from models.product_detector import ProductDetector
from models.facing_detector import FacingDetector
from models.gap_analyzer import GapAnalyzer
from utils.action_engine import ActionEngine

# ===== GESTION DES UTILISATEURS =====
USERS_FILE = "users.json"

def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        default_users = {"admin": {"password": "admin123", "created_at": str(datetime.now())}}
        save_users(default_users)
        return default_users

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def hash_password(password):
    salt = secrets.token_hex(8)
    return salt + ":" + hashlib.sha256((salt + password).encode()).hexdigest()

def verify_password(password, hashed):
    if ":" not in hashed:
        return password == hashed
    try:
        salt, hash_val = hashed.split(":")
        return hash_val == hashlib.sha256((salt + password).encode()).hexdigest()
    except:
        return False

def migrate_users():
    users = load_users()
    modified = False
    for username, data in users.items():
        if "password" in data and ":" not in data["password"]:
            data["password"] = hash_password(data["password"])
            modified = True
    if modified:
        save_users(users)

migrate_users()

# ===== INITIALISATION DES MODULES RETAIL =====
print("🔄 Chargement des modules Retail-Heros...")
detector = ProductDetector()
facing_detector = FacingDetector()
gap_analyzer = GapAnalyzer()
action_engine = ActionEngine()
print("✅ Modules chargés")

# ===== VARIABLES GLOBALES =====
current_user = None
analysis_counter = 0

# ===== FONCTIONS D'AUTHENTIFICATION =====
def login(username, password):
    global current_user
    users = load_users()
    if username in users and verify_password(password, users[username]["password"]):
        current_user = username
        return f"✅ Bienvenue {username} !", gr.update(visible=False), gr.update(visible=True), get_user_stats()
    return "❌ Identifiants incorrects", gr.update(visible=True), gr.update(visible=False), None

def logout():
    global current_user
    current_user = None
    return "👋 Déconnecté", gr.update(visible=True), gr.update(visible=False), None

def register(username, password):
    users = load_users()
    if username in users:
        return "❌ Nom déjà utilisé"
    if len(password) < 4:
        return "❌ Mot de passe trop court (min 4)"
    users[username] = {"password": hash_password(password), "created_at": str(datetime.now())}
    save_users(users)
    return "✅ Compte créé ! Connectez-vous."

def get_user_stats():
    if not current_user:
        return "🔒 Non connecté"
    users = load_users()
    if current_user not in users:
        return "❌ Utilisateur non trouvé"
    user_data = users[current_user]
    return f"""
### 👤 {current_user}
- 📅 Membre depuis: {user_data.get('created_at', 'N/A')[:10]}
- 📸 Analyses: {user_data.get('analyses_count', 0)}
- 📋 Dernières analyses: {len(user_data.get('history', []))}
"""

# ===== FONCTIONS D'ANALYSE =====
def analyze_image(image):
    global analysis_counter, current_user
    
    if image is None:
        return None, None, "❌ Aucune image fournie", ""
    
    try:
        gc.collect()
        analysis_counter += 1
        print(f"🔍 Analyse #{analysis_counter} en cours...")
        
        # 1. Détection des produits
        analysis = detector.analyze_shelf(image)
        
        if not analysis or not analysis.get('detections'):
            return None, None, "❌ Aucun produit détecté", ""
        
        # 2. Analyse des facings
        facing_analysis = facing_detector.count_facings(analysis['detections'], image.shape[1])
        analysis['facing_analysis'] = facing_analysis
        
        # 3. Détection des gaps (ruptures)
        gaps = gap_analyzer.detect_gaps(image, analysis['detections'])
        analysis['detected_gaps'] = gaps
        
        # 4. Génération des actions
        actions = action_engine.generate_actions(analysis)
        analysis['recommended_actions'] = actions
        
        # 5. Dashboard
        fig = create_dashboard(analysis)
        
        # 6. Métriques
        metrics = {
            'total_products': analysis.get('total_products', 0),
            'unique_products': analysis.get('unique_products', 0),
            'fill_rate': analysis.get('fill_rate', 0),
            'planogram_compliance': analysis.get('planogram_compliance', 0),
            'estimated_value': analysis.get('estimated_value', 0),
            'categories': len(analysis.get('categories', {})),
            'total_facings': facing_analysis.get('total_facings', 0),
            'gaps': len(gaps),
            'actions': len(actions)
        }
        
        # 7. Rapport
        report = generate_report(analysis, metrics, actions)
        
        # 8. Sauvegarde dans l'historique
        if current_user:
            users = load_users()
            if current_user in users:
                if 'history' not in users[current_user]:
                    users[current_user]['history'] = []
                users[current_user]['history'].append({
                    'timestamp': datetime.now().isoformat(),
                    'metrics': metrics
                })
                users[current_user]['analyses_count'] = users[current_user].get('analyses_count', 0) + 1
                save_users(users)
        
        gc.collect()
        return analysis['annotated_image'], fig, f"✅ Analyse #{analysis_counter} terminée", report
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()
        gc.collect()
        return None, None, f"❌ Erreur: {str(e)}", ""

def create_dashboard(analysis):
    """Crée le dashboard avec Plotly"""
    if not analysis or not analysis.get('detections'):
        fig = go.Figure()
        fig.add_annotation(
            text="📸 Upload une image pour voir le dashboard",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="gray")
        )
        fig.update_layout(height=500)
        return fig
    
    # Subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("📊 Catégories", "🏷️ Marques", "📈 Taux de remplissage", "💰 Valeur du stock")
    )
    
    # Catégories
    categories = analysis.get('categories', {})
    if categories:
        fig.add_trace(
            go.Pie(labels=list(categories.keys()), values=list(categories.values()), hole=0.3),
            row=1, col=1
        )
    
    # Marques
    brands = analysis.get('brands', {})
    if brands:
        sorted_brands = sorted(brands.items(), key=lambda x: x[1], reverse=True)[:5]
        fig.add_trace(
            go.Bar(x=[b[0] for b in sorted_brands], y=[b[1] for b in sorted_brands], marker_color='lightblue'),
            row=1, col=2
        )
    
    # Taux de remplissage
    fill_rate = analysis.get('fill_rate', 0)
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=fill_rate,
            title={'text': "Taux de remplissage"},
            gauge={
                'axis': {'range': [0, 100]},
                'steps': [
                    {'range': [0, 50], 'color': "red"},
                    {'range': [50, 75], 'color': "orange"},
                    {'range': [75, 100], 'color': "green"}
                ]
            }
        ),
        row=2, col=1
    )
    
    # Valeur
    estimated_value = analysis.get('estimated_value', 0)
    fig.add_trace(
        go.Indicator(mode="number", value=estimated_value, title={'text': "Valeur (€)"}),
        row=2, col=2
    )
    
    fig.update_layout(height=550, showlegend=True)
    return fig

def generate_report(analysis, metrics, actions):
    """Génère le rapport textuel"""
    report = f"""
### 📊 MÉTRIQUES GLOBALES
- **Total produits**: {metrics['total_products']}
- **Produits uniques**: {metrics['unique_products']}
- **Taux de remplissage**: {metrics['fill_rate']:.1f}%
- **Conformité planogramme**: {metrics['planogram_compliance']:.1f}%
- **Valeur du stock**: {metrics['estimated_value']:.2f}€
- **Catégories**: {metrics['categories']}
- **Total facings**: {metrics['total_facings']}
- **Ruptures détectées**: {metrics['gaps']}
- **Actions recommandées**: {metrics['actions']}

### 💡 ACTIONS RECOMMANDÉES
"""
    if actions:
        for action in actions[:5]:
            report += f"\n- {action.get('action', '')}"
    else:
        report += "\n✅ Tout est en ordre !"
    
    return report

# ===== INTERFACE GRADIO =====
with gr.Blocks(title="Retail-Heros", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🏪 Retail-Heros - Analyse de Rayons")
    
    # Section authentification
    with gr.Row():
        with gr.Column(scale=1, visible=True) as login_col:
            with gr.Tab("🔐 Connexion"):
                login_user = gr.Textbox(label="Nom")
                login_pass = gr.Textbox(label="Mot de passe", type="password")
                login_btn = gr.Button("Se connecter")
                login_msg = gr.Markdown("")
            
            with gr.Tab("📝 Inscription"):
                reg_user = gr.Textbox(label="Nom")
                reg_pass = gr.Textbox(label="Mot de passe", type="password")
                reg_btn = gr.Button("Créer un compte")
                reg_msg = gr.Markdown("")
            
            logout_btn = gr.Button("🚪 Déconnexion", visible=False)
        
        with gr.Column(scale=1, visible=False) as user_col:
            user_stats = gr.Markdown("### 👤 Profil")
    
    gr.Markdown("---")
    
    # Section analyse
    with gr.Row():
        with gr.Column(scale=1):
            input_image = gr.Image(
                label="📸 Upload une photo de rayon",
                type="numpy",
                sources=["upload"],
                height=400
            )
            analyze_btn = gr.Button("🚀 Analyser", variant="primary", size="lg")
            status = gr.Textbox(label="Statut", value="Prêt")
        
        with gr.Column(scale=1):
            output_image = gr.Image(label="🖼️ Résultat détection", height=400)
    
    with gr.Row():
        with gr.Column(scale=1):
            report = gr.Markdown("📋 **Rapport**\n\nUpload une image pour commencer.")
        
        with gr.Column(scale=2):
            dashboard = gr.Plot(label="📊 Dashboard")
    
    # Événements
    login_btn.click(login, [login_user, login_pass], [login_msg, login_col, user_col, user_stats])
    logout_btn.click(logout, None, [login_msg, login_col, user_col, user_stats])
    reg_btn.click(register, [reg_user, reg_pass], reg_msg)
    analyze_btn.click(analyze_image, [input_image], [output_image, dashboard, status, report])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print("🚀 Lancement de Retail-Heros...")
    demo.launch(server_name="0.0.0.0", server_port=port, share=False)
