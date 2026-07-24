import sys
import traceback
import os

print("="*60)
print("🚀 Démarrage de Retail-Heros...")
print(f"📁 Dossier courant : {os.getcwd()}")
print(f"📄 Fichiers présents : {os.listdir('.')}")
print("="*60)

try:
    import gradio as gr
    import json
    from datetime import datetime
    import gc
    import torch

    # Optimisations mémoire
    os.environ['YOLO_VERBOSE'] = 'False'
    os.environ['ULTRALYTICS_MEMORY_LIMIT'] = '256'
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    print("✅ Imports réussis")

    # Modules Retail
    from models.product_detector import ProductDetector
    from models.facing_detector import FacingDetector
    from models.gap_analyzer import GapAnalyzer
    from utils.action_engine import ActionEngine
    from auth import UserManager
    from dashboard import RetailDashboard

    print("✅ Modules Retail importés")

    # Initialisation
    detector = ProductDetector()
    facing_detector = FacingDetector()
    gap_analyzer = GapAnalyzer()
    action_engine = ActionEngine()
    user_manager = UserManager()
    dashboard = RetailDashboard()

    print("✅ Modules initialisés")

    # Variables globales
    current_session = None
    current_user = None
    analysis_counter = 0

    # ===== FONCTIONS AUTH =====
    def login_user(username, password):
        global current_session, current_user
        if not username or not password:
            return "❌ Remplissez tous les champs", None, None, None
        
        success, session_token, message = user_manager.login(username, password)
        if success:
            current_session = session_token
            current_user = username
            stats = get_user_stats_ui()
            return f"✅ {message}", stats, gr.update(visible=False), gr.update(visible=True)
        else:
            return f"❌ {message}", None, gr.update(visible=True), gr.update(visible=False)

    def logout_user():
        global current_session, current_user
        if current_session:
            user_manager.logout(current_session)
        current_session = None
        current_user = None
        return "👋 Déconnecté", gr.update(visible=True), gr.update(visible=False), None

    def register_user(username, password):
        if not username or not password:
            return "❌ Remplissez tous les champs"
        success, message = user_manager.create_user(username, password)
        return f"{'✅' if success else '❌'} {message}"

    def get_user_stats_ui():
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
            recent = "\n- Aucune analyse"
        # CORRECTION : utilisation de guillemets doubles à l'intérieur de la f-string
        return f"### 👤 {stats['username']}\n- 📧 {stats.get('email', "Pas d'email")}\n- 📸 Analyses: {stats.get('analyses_count', 0)}\n- 📋 Dernières:{recent}"

    # ===== FONCTIONS ANALYSE =====
    def analyze_image(image):
        global analysis_counter, current_user
        
        if image is None:
            return None, None, "❌ Aucune image fournie", ""
        
        try:
            gc.collect()
            analysis_counter += 1
            print(f"🔍 Analyse #{analysis_counter} en cours...")
            
            analysis = detector.analyze_shelf(image)
            
            if not analysis or not analysis.get('detections') or len(analysis['detections']) == 0:
                return None, dashboard.create_dashboard(None), "❌ Aucun produit détecté. Essayez une autre image.", ""
            
            facing_analysis = facing_detector.count_facings(analysis['detections'], image.shape[1])
            analysis['facing_analysis'] = facing_analysis
            
            gaps = gap_analyzer.detect_gaps(image, analysis['detections'])
            analysis['detected_gaps'] = gaps
            
            actions = action_engine.generate_actions(analysis)
            analysis['recommended_actions'] = actions
            
            fig = dashboard.create_dashboard(analysis)
            
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

### 💡 ACTIONS RECOMMANDÉES
"""
            if actions:
                for action in actions[:5]:
                    report += f"\n- {action.get('action', '')}"
            else:
                report += "\n✅ Tout est en ordre !"
            
            if current_user:
                user_manager.add_analysis_history(current_user, {
                    'timestamp': str(datetime.now()),
                    'total_products': analysis.get('total_products', 0)
                })
            
            status_text = f"✅ Analyse #{analysis_counter} réussie : {metrics['total_products']} produits détectés (unique: {metrics['unique_products']})"
            
            gc.collect()
            return analysis['annotated_image'], fig, status_text, report
            
        except Exception as e:
            print(f"❌ Erreur analyse: {str(e)}")
            import traceback
            traceback.print_exc()
            gc.collect()
            return None, dashboard.create_dashboard(None), f"❌ Erreur: {str(e)}", ""

    # ===== INTERFACE GRADIO =====
    print("🔄 Création de l'interface Gradio...")
    with gr.Blocks(title="Retail-Heros", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 🏪 Retail-Heros - Analyse de Rayons")
        
        # Auth
        with gr.Row():
            with gr.Column(scale=1, visible=True) as login_col:
                with gr.Tab("🔐 Connexion"):
                    login_user_input = gr.Textbox(label="Nom", placeholder="admin")
                    login_pass_input = gr.Textbox(label="Mot de passe", type="password", placeholder="admin123")
                    login_btn = gr.Button("Se connecter", variant="primary")
                    login_msg = gr.Markdown("")
                
                with gr.Tab("📝 Inscription"):
                    reg_user_input = gr.Textbox(label="Nom", placeholder="Choisissez un nom")
                    reg_pass_input = gr.Textbox(label="Mot de passe", type="password", placeholder="Min 4 caractères")
                    reg_btn = gr.Button("S'inscrire", variant="secondary")
                    reg_msg = gr.Markdown("")
                
                logout_btn = gr.Button("🚪 Déconnexion", variant="stop", visible=False)
            
            with gr.Column(scale=1, visible=False) as user_col:
                user_stats = gr.Markdown("### 👤 Profil")
                refresh_stats = gr.Button("🔄 Rafraîchir", variant="secondary", size="sm")
        
        gr.Markdown("---")
        
        # Analyse
        with gr.Row():
            with gr.Column(scale=1):
                input_image = gr.Image(
                    label="📸 Upload une photo de rayon",
                    type="numpy",
                    height=400
                )
                analyze_btn = gr.Button("🚀 Analyser", variant="primary", size="lg")
                status = gr.Textbox(label="Statut", value="Prêt à analyser")
            
            with gr.Column(scale=1):
                output_image = gr.Image(label="🖼️ Résultat détection", height=400)
        
        with gr.Row():
            with gr.Column(scale=1):
                report = gr.Markdown("📋 **Rapport**\n\nUpload une image pour commencer.")
            
            with gr.Column(scale=2):
                dashboard_plot = gr.Plot(label="📊 Dashboard")
        
        # Événements
        login_btn.click(login_user, [login_user_input, login_pass_input], [login_msg, user_stats, login_col, user_col])
        logout_btn.click(logout_user, None, [login_msg, login_col, user_col, user_stats])
        reg_btn.click(register_user, [reg_user_input, reg_pass_input], reg_msg)
        refresh_stats.click(get_user_stats_ui, None, user_stats)
        analyze_btn.click(analyze_image, [input_image], [output_image, dashboard_plot, status, report])

    print("✅ Interface Gradio créée")

    # ===== LANCEMENT =====
    if __name__ == "__main__":
        port = int(os.environ.get("PORT", 10000))
        print(f"🚀 Lancement sur le port {port}")
        demo.launch(
            server_name="0.0.0.0",
            server_port=port,
            share=False,
            root_path="/"
        )

except Exception as e:
    print("="*60)
    print("❌ ERREUR AU DÉMARRAGE")
    print("="*60)
    traceback.print_exc()
    print("="*60)
    sys.stdout.flush()
    sys.stderr.flush()
    sys.exit(1)
