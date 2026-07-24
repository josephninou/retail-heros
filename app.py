import gradio as gr
import cv2
import numpy as np
from PIL import Image
import plotly.graph_objects as go
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

from models.product_detector import ProductDetector
from models.facing_detector import FacingDetector
from models.gap_analyzer import GapAnalyzer
from utils.action_engine import ActionEngine
from dashboard import RetailDashboard
from auth import UserManager

print("="*60)
print("🏪 Retail-Heros - Démarrage sur Render")
print("="*60)

# Initialisation des modules
print("🔄 Initialisation des modules...")
detector = ProductDetector()
facing_detector = FacingDetector()
gap_analyzer = GapAnalyzer()
action_engine = ActionEngine()
dashboard = RetailDashboard()
user_manager = UserManager()

# Variables globales
analysis_counter = 0
current_session = None
current_user = None

# ======================================================
# FONCTIONS D'ANALYSE
# ======================================================

def process_shelf_image(image):
    global analysis_counter
    
    if image is None:
        return None, None, dashboard.create_empty_dashboard(), "❌ Aucune image fournie", ""
    
    try:
        gc.collect()
        analysis_counter += 1
        print(f"\n🔍 Analyse #{analysis_counter} en cours...")
        
        # 1. Détection
        analysis = detector.analyze_shelf(image)
        
        if not analysis or not analysis.get('detections'):
            return None, None, dashboard.create_empty_dashboard(), "❌ Aucun produit détecté", ""
        
        # 2. Facings
        facing_analysis = facing_detector.count_facings(analysis['detections'], image.shape[1])
        analysis['facing_analysis'] = facing_analysis
        
        # 3. Gaps
        gaps = gap_analyzer.detect_gaps(image, analysis['detections'])
        analysis['detected_gaps'] = gaps
        
        # 4. Actions
        actions = action_engine.generate_actions(analysis)
        analysis['recommended_actions'] = actions
        
        # 5. Dashboard
        dashboard_fig = dashboard.create_dashboard(analysis)
        
        # 6. Métriques
        metrics = dashboard.create_performance_metrics(analysis)
        
        # 7. Rapport
        report = generate_comprehensive_report(analysis, metrics, actions)
        
        # 8. Sauvegarder dans l'historique de l'utilisateur
        if current_user:
            user_manager.add_analysis_history(current_user, {
                'timestamp': datetime.now().isoformat(),
                'metrics': metrics,
                'total_products': analysis.get('total_products', 0),
                'fill_rate': analysis.get('fill_rate', 0)
            })
        
        gc.collect()
        
        user_msg = f"✅ Analyse terminée ! 👋 {current_user if current_user else 'Invité'}"
        
        return analysis['annotated_image'], dashboard_fig, report, user_msg, json.dumps(metrics, indent=2)
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()
        gc.collect()
        return None, None, dashboard.create_empty_dashboard(), f"❌ Erreur: {str(e)}", ""

def generate_comprehensive_report(analysis, metrics, actions):
    """Génère un rapport complet"""
    report = f"""
# 📋 RAPPORT COMPLET - ANALYSE RAYON

---

### 📊 MÉTRIQUES GLOBALES

| Métrique | Valeur | Statut |
|----------|--------|--------|
| **Total Produits** | {metrics.get('Total Produits', 0)} | ✅ |
| **Produits Uniques** | {metrics.get('Produits Uniques', 0)} | ✅ |
| **Taux de Remplissage** | {metrics.get('Taux Remplissage', '0%')} | {get_status_emoji(metrics.get('Taux Remplissage', '0%'))} |
| **Conformité Planogramme** | {metrics.get('Conformité Planogramme', '0%')} | {get_status_emoji(metrics.get('Conformité Planogramme', '0%'))} |
| **Valeur Stock** | {metrics.get('Valeur Stock', '0€')} | 💰 |
| **Catégories** | {metrics.get('Catégories', 0)} | ✅ |
| **Total Facings** | {analysis.get('facing_analysis', {}).get('total_facings', 0)} | 📦 |
| **Ruptures** | {len(analysis.get('detected_gaps', []))} | ⚠️ |

---

### 📦 DÉTAIL DES PRODUITS

#### Par Catégorie
"""
    
    for category, count in analysis.get('categories', {}).items():
        report += f"\n- **{category}**: {count} produit(s)"
    
    report += f"""
    
#### Part de Linéaire (Share of Shelf)
"""
    
    share_of_shelf = analysis.get('facing_analysis', {}).get('share_of_shelf', {})
    if share_of_shelf:
        sorted_products = sorted(share_of_shelf.items(), key=lambda x: x[1], reverse=True)[:5]
        for product, sos in sorted_products:
            report += f"\n- **{product}**: {sos:.1f}% du linéaire"
    else:
        report += "\n- Aucune donnée disponible"
    
    report += f"""
    
### 💡 ACTIONS RECOMMANDÉES ({len(actions)})
"""
    
    if actions:
        for i, action in enumerate(actions[:5], 1):
            priority_emoji = {
                'urgent': '🔴',
                'high': '🟡',
                'medium': '🟠',
                'low': '🟢'
            }.get(action.get('priority', 'low'), '⚪')
            
            report += f"""
{i}. {priority_emoji} **{action.get('type', 'action').upper()}** - {action.get('action', '')}
   *Priorité: {action.get('priority', 'low')}*
"""
    else:
        report += "\n✅ Aucune action recommandée !"
    
    report += f"""
    
### 🔍 RUPTURES DÉTECTÉES ({len(analysis.get('detected_gaps', []))})
"""
    
    for i, gap in enumerate(analysis.get('detected_gaps', [])[:3], 1):
        report += f"\n{i}. Espace vide détecté"
        if gap.get('expected_product'):
            report += f" (Produit: {gap['expected_product']})"
    
    report += f"""

---
*Rapport généré par Retail-Heros*
*Date: {datetime.now().strftime("%d/%m/%Y à %H:%M")}*
"""
    
    return report

def get_status_emoji(value):
    if isinstance(value, str):
        try:
            value = float(value.replace('%', ''))
        except:
            return "⚪"
    if value >= 80:
        return "🟢"
    elif value >= 60:
        return "🟡"
    else:
        return "🔴"

# ======================================================
# FONCTIONS D'AUTHENTIFICATION
# ======================================================

def login_user(username, password):
    global current_session, current_user
    
    if not username or not password:
        return "❌ Veuillez remplir tous les champs", None, None, None, None
    
    success, session_token, message = user_manager.login(username, password)
    
    if success:
        current_session = session_token
        current_user = username
        stats = get_user_stats_ui()
        return f"✅ {message}", stats, gr.update(visible=False), gr.update(visible=True), gr.update(visible=True)
    else:
        return f"❌ {message}", None, gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)

def logout_user():
    global current_session, current_user
    
    if current_session:
        user_manager.logout(current_session)
    
    current_session = None
    current_user = None
    
    return "👋 Déconnecté", gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), None

def register_user(username, password, email):
    if not username or not password:
        return "❌ Veuillez remplir tous les champs"
    
    if len(username) < 3:
        return "❌ Le nom d'utilisateur doit faire au moins 3 caractères"
    
    if len(password) < 6:
        return "❌ Le mot de passe doit faire au moins 6 caractères"
    
    if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return "❌ Email invalide"
    
    success, message = user_manager.create_user(username, password, email)
    
    if success:
        return f"✅ {message}. Connectez-vous maintenant !"
    else:
        return f"❌ {message}"

def get_user_stats_ui():
    if not current_user:
        return "🔒 Veuillez vous connecter"
    
    stats = user_manager.get_user_stats(current_user)
    if not stats:
        return "❌ Utilisateur non trouvé"
    
    recent = ""
    if stats.get('recent_analyses'):
        for a in stats['recent_analyses'][-3:]:
            date = a.get('timestamp', '')[:16]
            products = a.get('data', {}).get('total_products', 0)
            recent += f"\n- {date}: {products} produits"
    else:
        recent = "\n- Aucune analyse"
    
    return f"""
## 👤 {stats['username']}

📧 **Email**: {stats.get('email', 'Non renseigné')}
📅 **Membre depuis**: {stats.get('created_at', 'N/A')[:10] if stats.get('created_at') else 'N/A'}
🔐 **Dernière connexion**: {stats.get('last_login', 'Jamais')[:16] if stats.get('last_login') else 'Jamais'}
📸 **Analyses réalisées**: {stats.get('analyses_count', 0)}

### 📋 Dernières analyses
{recent}
"""

# ======================================================
# FONCTIONS DE RÉINITIALISATION DU MOT DE PASSE
# ======================================================

def request_password_reset(username_or_email):
    if not username_or_email:
        return "❌ Veuillez entrer votre nom d'utilisateur ou email"
    
    success, token, email = user_manager.generate_reset_token(username_or_email)
    
    if not success:
        return f"❌ {token}"
    
    reset_link = f"https://retail-heros.onrender.com/reset?token={token}"
    
    return f"""
✅ Un lien de réinitialisation a été envoyé à **{email}**

🔗 **Lien de réinitialisation (simulé)** :  
`{reset_link}`

⚠️ Ce lien expire dans 24 heures.
"""

def reset_password_confirm(token, new_password, confirm_password):
    if not token:
        return "❌ Token manquant"
    
    if new_password != confirm_password:
        return "❌ Les mots de passe ne correspondent pas"
    
    if len(new_password) < 6:
        return "❌ Le mot de passe doit faire au moins 6 caractères"
    
    success, message = user_manager.reset_password(token, new_password)
    
    if success:
        return f"✅ {message}. Vous pouvez maintenant vous connecter."
    else:
        return f"❌ {message}"

# ======================================================
# INTERFACE GRADIO
# ======================================================

def create_app():
    with gr.Blocks(
        title="Retail-Heros - Analyse Rayon",
        theme=gr.themes.Soft(),
        css="""
            .gradio-container {max-width: 1400px !important; margin: auto;}
            .login-box {background: #f0f4ff; padding: 20px; border-radius: 10px; border: 2px solid #4a90d9;}
            .stats-box {background: #e8f5e9; padding: 15px; border-radius: 10px;}
            .report-box {background: #f8f9fa; padding: 20px; border-radius: 10px; max-height: 400px; overflow-y: auto;}
            .header-title {text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white;}
        """
    ) as demo:
        
        gr.Markdown("""
        <div class="header-title">
            <h1>🏪 Retail-Heros</h1>
            <p>Solution d'analyse de rayons pour le retail</p>
        </div>
        """)
        
        # AUTH SECTION
        with gr.Row():
            with gr.Column(scale=1, visible=True) as login_section:
                gr.Markdown("### 🔐 Connexion / Inscription")
                
                with gr.Tabs():
                    with gr.TabItem("🔐 Se connecter"):
                        login_username = gr.Textbox(label="Nom d'utilisateur", placeholder="Entrez votre nom")
                        login_password = gr.Textbox(label="Mot de passe", type="password", placeholder="••••••••")
                        login_btn = gr.Button("🚀 Se connecter", variant="primary", size="lg")
                        login_result = gr.Markdown("")
                    
                    with gr.TabItem("📝 S'inscrire"):
                        reg_username = gr.Textbox(label="Nom d'utilisateur", placeholder="Choisissez un nom (min 3)")
                        reg_password = gr.Textbox(label="Mot de passe", type="password", placeholder="Minimum 6 caractères")
                        reg_email = gr.Textbox(label="Email (optionnel)", placeholder="email@exemple.com")
                        reg_btn = gr.Button("✅ S'inscrire", variant="secondary", size="lg")
                        reg_result = gr.Markdown("")
                    
                    with gr.TabItem("🔄 Mot de passe oublié"):
                        reset_input = gr.Textbox(label="Nom d'utilisateur ou Email", placeholder="Entrez votre nom ou email")
                        reset_request_btn = gr.Button("📧 Envoyer le lien", variant="secondary", size="lg")
                        reset_result = gr.Markdown("")
                        
                        gr.Markdown("---")
                        reset_token_input = gr.Textbox(label="Token de réinitialisation", placeholder="Collez votre token")
                        reset_new_password = gr.Textbox(label="Nouveau mot de passe", type="password", placeholder="Minimum 6 caractères")
                        reset_confirm_password = gr.Textbox(label="Confirmer", type="password", placeholder="Confirmez")
                        reset_confirm_btn = gr.Button("🔑 Réinitialiser", variant="primary", size="lg")
                        reset_confirm_result = gr.Markdown("")
                
                logout_btn = gr.Button("🚪 Se déconnecter", variant="stop", visible=False, size="lg")
            
            with gr.Column(scale=1, visible=False) as user_section:
                gr.Markdown("### 👤 Mon Profil")
                user_stats = gr.Markdown("📊 Statistiques utilisateur", elem_classes="stats-box")
                refresh_stats_btn = gr.Button("🔄 Rafraîchir", variant="secondary", size="sm")
        
        # ANALYSE SECTION
        gr.Markdown("---")
        gr.Markdown("## 📸 Analyse du rayon")
        
        with gr.Row():
            with gr.Column(scale=1):
                input_image = gr.Image(
                    label="📸 Upload une photo de rayon",
                    type="numpy",
                    sources=["upload", "webcam"],
                    height=450
                )
                analyze_btn = gr.Button("🚀 Analyser le rayon", variant="primary", size="lg")
                status = gr.Textbox(label="Statut", interactive=False, value="Prêt - Connectez-vous pour sauvegarder vos analyses")
            
            with gr.Column(scale=1):
                output_image = gr.Image(
                    label="🖼️ Résultat Détection",
                    type="numpy",
                    height=450
                )
        
        with gr.Row():
            with gr.Column(scale=1):
                report = gr.Markdown("📋 **Rapport d'analyse**\n\nUpload une image pour commencer.", elem_classes="report-box")
            
            with gr.Column(scale=2):
                dashboard_output = gr.Plot(label="📊 Dashboard Complet")
        
        metrics_json = gr.JSON(label="📊 Métriques détaillées", visible=False)
        
        # ===== CONNEXIONS =====
        login_btn.click(
            fn=login_user,
            inputs=[login_username, login_password],
            outputs=[login_result, user_stats, login_section, user_section, logout_btn]
        )
        
        reg_btn.click(
            fn=register_user,
            inputs=[reg_username, reg_password, reg_email],
            outputs=reg_result
        )
        
        logout_btn.click(
            fn=logout_user,
            outputs=[login_result, login_section, user_section, logout_btn, user_stats]
        )
        
        reset_request_btn.click(
            fn=request_password_reset,
            inputs=reset_input,
            outputs=reset_result
        )
        
        reset_confirm_btn.click(
            fn=reset_password_confirm,
            inputs=[reset_token_input, reset_new_password, reset_confirm_password],
            outputs=reset_confirm_result
        )
        
        refresh_stats_btn.click(
            fn=get_user_stats_ui,
            outputs=user_stats
        )
        
        analyze_btn.click(
            fn=process_shelf_image,
            inputs=input_image,
            outputs=[output_image, dashboard_output, report, status, metrics_json]
        )
        
        input_image.change(
            fn=lambda x: "📸 Image chargée, prêt à analyser !",
            inputs=None,
            outputs=status
        )
    
    return demo

# ======================================================
# LANCEMENT - CORRIGÉ POUR RENDER
# ======================================================

if __name__ == "__main__":
    # Récupérer le port depuis les variables d'environnement
    port = int(os.environ.get("PORT", 10000))
    
    print(f"🚀 Démarrage sur le port {port}")
    print(f"🌐 URL: https://retail-heros.onrender.com")
    
    demo = create_app()
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,
        debug=False,
        show_error=True
    )
