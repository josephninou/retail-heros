import gradio as gr
import cv2
import numpy as np
from PIL import Image
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime
import json
import os
import gc
import torch
import hashlib
import secrets
import re

# Optimisations mémoire
os.environ['YOLO_VERBOSE'] = 'False'
os.environ['ULTRALYTICS_MEMORY_LIMIT'] = '256'
if torch.cuda.is_available():
    torch.cuda.empty_cache()

# Import des modules
from models.product_detector import ProductDetector
from models.facing_detector import FacingDetector
from models.gap_analyzer import GapAnalyzer
from utils.action_engine import ActionEngine
from auth import UserManager

print("="*60)
print("🏪 Retail-Heros - Démarrage sur Render")
print("="*60)

# Initialisation
print("🔄 Initialisation des modules...")
detector = ProductDetector()
facing_detector = FacingDetector()
gap_analyzer = GapAnalyzer()
action_engine = ActionEngine()
user_manager = UserManager()

# Variables
analysis_counter = 0
current_session = None
current_user = None

# ===================================================
# DASHBOARD SIMPLIFIÉ
# ===================================================

def create_dashboard(analysis_data):
    """Crée un dashboard simple avec Plotly"""
    
    if not analysis_data or not analysis_data.get('detections'):
        fig = go.Figure()
        fig.add_annotation(
            text="📸 Upload une image pour voir le dashboard",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=24, color="gray")
        )
        fig.update_layout(height=500)
        return fig
    
    # Créer des subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "📊 Catégories",
            "🏷️ Marques",
            "📈 Taux de remplissage",
            "💰 Valeur du stock"
        )
    )
    
    # Catégories
    categories = analysis_data.get('categories', {})
    if categories:
        fig.add_trace(
            go.Pie(
                labels=list(categories.keys()),
                values=list(categories.values()),
                hole=0.3
            ),
            row=1, col=1
        )
    
    # Marques
    brands = analysis_data.get('brands', {})
    if brands:
        sorted_brands = sorted(brands.items(), key=lambda x: x[1], reverse=True)[:5]
        fig.add_trace(
            go.Bar(
                x=[b[0] for b in sorted_brands],
                y=[b[1] for b in sorted_brands],
                marker_color='lightblue'
            ),
            row=1, col=2
        )
    
    # Taux de remplissage
    fill_rate = analysis_data.get('fill_rate', 0)
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
    estimated_value = analysis_data.get('estimated_value', 0)
    fig.add_trace(
        go.Indicator(
            mode="number",
            value=estimated_value,
            title={'text': "Valeur du stock (€)"}
        ),
        row=2, col=2
    )
    
    fig.update_layout(height=600, showlegend=True)
    return fig

# ===================================================
# AUTHENTIFICATION
# ===================================================

def login_user(username, password):
    global current_session, current_user
    
    if not username or not password:
        return "❌ Remplissez tous les champs", None, None, None
    
    success, session_token, message = user_manager.login(username, password)
    
    if success:
        current_session = session_token
        current_user = username
        return f"✅ {message}", gr.update(visible=False), gr.update(visible=True), get_user_stats()
    else:
        return f"❌ {message}", gr.update(visible=True), gr.update(visible=False), None

def logout_user():
    global current_session, current_user
    
    if current_session:
        user_manager.logout(current_session)
    current_session = None
    current_user = None
    
    return "👋 Déconnecté", gr.update(visible=True), gr.update(visible=False), None

def register_user(username, password, email):
    if not username or not password:
        return "❌ Remplissez tous les champs"
    
    if len(username) < 3:
        return "❌ Nom trop court (min 3)"
    
    if len(password) < 6:
        return "❌ Mot de passe trop court (min 6)"
    
    success, message = user_manager.create_user(username, password, email)
    return f"{'✅' if success else '❌'} {message}"

def get_user_stats():
    if not current_user:
        return "🔒 Non connecté"
    
    stats = user_manager.get_user_stats(current_user)
    if not stats:
        return "❌ Utilisateur non trouvé"
    
    recent = ""
    for a in stats.get('recent_analyses', [])[-3:]:
        products = a.get('data', {}).get('total_products', 0)
        recent = recent + f"\n- {a.get('timestamp', '')[:16]}: {products} produits"
    
    if not recent:
        recent = "\n- Aucune"
    
    result = f"""
### 👤 {stats['username']}
- 📧 {stats.get('email', 'Pas d\'email')}
- 📅 Membre depuis: {stats.get('created_at', '')[:10]}
- 📸 Analyses: {stats.get('analyses_count', 0)}
- 📋 Dernières:{recent}
"""
    return result

# ===================================================
# ANALYSE
# ===================================================

def process_image(image):
    global analysis_counter
    
    if image is None:
        return None, create_dashboard(None), "❌ Aucune image", ""
    
    try:
        gc.collect()
        analysis_counter = analysis_counter + 1
        print(f"🔍 Analyse #{analysis_counter}")
        
        # Détection
        analysis = detector.analyze_shelf(image)
        
        if not analysis or not analysis.get('detections'):
            return None, create_dashboard(None), "❌ Aucun produit détecté", ""
        
        # Facings
        facing_analysis = facing_detector.count_facings(analysis['detections'], image.shape[1])
        analysis['facing_analysis'] = facing_analysis
        
        # Gaps
        gaps = gap_analyzer.detect_gaps(image, analysis['detections'])
        analysis['detected_gaps'] = gaps
        
        # Actions
        actions = action_engine.generate_actions(analysis)
        analysis['recommended_actions'] = actions
        
        # Dashboard
        fig = create_dashboard(analysis)
        
        # Métriques
        metrics = {
            'produits': analysis.get('total_products', 0),
            'taux_remplissage': f"{analysis.get('fill_rate', 0):.1f}%",
            'valeur': f"{analysis.get('estimated_value', 0):.2f}€",
            'facings': facing_analysis.get('total_facings', 0),
            'ruptures': len(gaps)
        }
        
        # Sauvegarder
        if current_user:
            user_manager.add_analysis_history(current_user, {
                'timestamp': datetime.now().isoformat(),
                'total_products': analysis.get('total_products', 0)
            })
        
        # Rapport
        report = f"""
### 📊 RÉSULTATS
- **Produits**: {metrics['produits']}
- **Taux de remplissage**: {metrics['taux_remplissage']}
- **Valeur du stock**: {metrics['valeur']}
- **Facings**: {metrics['facings']}
- **Ruptures**: {metrics['ruptures']}

### 💡 ACTIONS ({len(actions)})
"""
        for action in actions[:3]:
            report = report + f"\n- {action.get('action', '')}"
        
        if not actions:
            report = report + "\n✅ Tout est en ordre !"
        
        gc.collect()
        return analysis['annotated_image'], fig, f"✅ Analyse #{analysis_counter} terminée", report
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()
        gc.collect()
        return None, create_dashboard(None), f"❌ Erreur: {str(e)}", ""

# ===================================================
# INTERFACE GRADIO SIMPLIFIÉE
# ===================================================

def create_app():
    with gr.Blocks(title="Retail-Heros", theme=gr.themes.Soft()) as demo:
        
        gr.Markdown("""
        # 🏪 Retail-Heros
        ### Analyse de rayons pour le retail
        """)
        
        # Auth
        with gr.Row():
            with gr.Column(scale=1, visible=True) as login_col:
                with gr.Tab("🔐 Connexion"):
                    login_user_input = gr.Textbox(label="Nom", placeholder="admin")
                    login_pass_input = gr.Textbox(label="Mot de passe", type="password", placeholder="admin123")
                    login_btn = gr.Button("Se connecter", variant="primary")
                    login_msg = gr.Markdown("")
                
                with gr.Tab("📝 Inscription"):
                    reg_user = gr.Textbox(label="Nom", placeholder="Choisissez un nom")
                    reg_pass = gr.Textbox(label="Mot de passe", type="password", placeholder="Min 6 caractères")
                    reg_email = gr.Textbox(label="Email (optionnel)", placeholder="email@exemple.com")
                    reg_btn = gr.Button("S'inscrire", variant="secondary")
                    reg_msg = gr.Markdown("")
                
                logout_btn = gr.Button("🚪 Déconnexion", variant="stop", visible=False)
            
            with gr.Column(scale=1, visible=False) as user_col:
                user_stats = gr.Markdown("### 👤 Profil")
        
        gr.Markdown("---")
        
        # Analyse
        with gr.Row():
            with gr.Column(scale=1):
                input_img = gr.Image(
                    label="📸 Upload une photo",
                    type="numpy",
                    sources=["upload", "webcam"],
                    height=400
                )
                analyze_btn = gr.Button("🚀 Analyser", variant="primary", size="lg")
                status = gr.Textbox(label="Statut", value="Prêt")
            
            with gr.Column(scale=1):
                output_img = gr.Image(label="🖼️ Résultat", height=400)
        
        with gr.Row():
            with gr.Column(scale=1):
                report = gr.Markdown("📋 **Rapport**\n\nUpload une image")
            
            with gr.Column(scale=2):
                dashboard = gr.Plot(label="📊 Dashboard")
        
        # Connexions
        login_btn.click(
            fn=login_user,
            inputs=[login_user_input, login_pass_input],
            outputs=[login_msg, login_col, user_col, user_stats]
        )
        
        reg_btn.click(
            fn=register_user,
            inputs=[reg_user, reg_pass, reg_email],
            outputs=reg_msg
        )
        
        logout_btn.click(
            fn=logout_user,
            outputs=[login_msg, login_col, user_col, user_stats]
        )
        
        analyze_btn.click(
            fn=process_image,
            inputs=input_img,
            outputs=[output_img, dashboard, status, report]
        )
    
    return demo

# ===================================================
# LANCEMENT
# ===================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Démarrage sur le port {port}")
    
    demo = create_app()
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,
        debug=False
    )
