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

# Optimisations mémoire
os.environ['YOLO_VERBOSE'] = 'False'
os.environ['ULTRALYTICS_MEMORY_LIMIT'] = '256'
torch.cuda.empty_cache() if torch.cuda.is_available() else None

from models.product_detector import ProductDetector
from models.facing_detector import FacingDetector
from models.gap_analyzer import GapAnalyzer
from utils.action_engine import ActionEngine
from dashboard import RetailDashboard

print("="*50)
print("🏪 Retail-Heros - Démarrage sur Render")
print(f"RAM disponible: {os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / (1024.**3):.2f} GB")
print("="*50)

# Initialisation des modules
print("🔄 Initialisation des modules...")
detector = ProductDetector()
facing_detector = FacingDetector()
gap_analyzer = GapAnalyzer()
action_engine = ActionEngine()
dashboard = RetailDashboard()

analysis_history = []
analysis_counter = 0

def process_shelf_image(image):
    global analysis_counter
    
    if image is None:
        return None, None, dashboard.create_empty_dashboard(), "❌ Aucune image fournie", ""
    
    try:
        # Nettoyer la mémoire avant l'analyse
        gc.collect()
        
        analysis_counter += 1
        print(f"\n{'='*50}")
        print(f"🔍 Analyse #{analysis_counter} en cours...")
        
        # 1. Détection des produits
        print("📦 Détection des produits...")
        analysis = detector.analyze_shelf(image)
        
        if not analysis or not analysis.get('detections'):
            return None, None, dashboard.create_empty_dashboard(), "❌ Aucun produit détecté", ""
        
        # 2. Analyse des facings
        print("📊 Analyse des facings...")
        facing_analysis = facing_detector.count_facings(
            analysis['detections'], 
            image.shape[1]
        )
        analysis['facing_analysis'] = facing_analysis
        
        # 3. Analyse des gaps
        print("🔍 Détection des ruptures...")
        gaps = gap_analyzer.detect_gaps(image, analysis['detections'])
        analysis['detected_gaps'] = gaps
        
        # 4. Génération des actions
        print("💡 Génération des recommandations...")
        actions = action_engine.generate_actions(analysis)
        analysis['recommended_actions'] = actions
        
        # 5. Dashboard
        print("📊 Génération du dashboard...")
        dashboard_fig = dashboard.create_dashboard(analysis)
        
        # 6. Métriques
        metrics = dashboard.create_performance_metrics(analysis)
        
        # 7. Rapport
        report = generate_comprehensive_report(analysis, metrics, actions)
        
        # 8. Historique
        analysis_history.append({
            'id': analysis_counter,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'metrics': metrics,
            'analysis': analysis
        })
        
        print("✅ Analyse terminée !")
        print(f"📊 {analysis['total_products']} produits détectés")
        
        # Nettoyer la mémoire
        gc.collect()
        
        return analysis['annotated_image'], dashboard_fig, report, "✅ Analyse terminée !", json.dumps(metrics, indent=2)
        
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
## Retail-Heros v2.0 (Render)

---

### 📊 MÉTRIQUES GLOBALES

| Métrique | Valeur | Statut |
|----------|--------|--------|
| **Total Produits** | {metrics['Total Produits']} | ✅ |
| **Produits Uniques** | {metrics['Produits Uniques']} | ✅ |
| **Taux de Remplissage** | {metrics['Taux Remplissage']} | {get_status_emoji(metrics['Taux Remplissage'])} |
| **Conformité Planogramme** | {metrics['Conformité Planogramme']} | {get_status_emoji(metrics['Conformité Planogramme'])} |
| **Valeur Stock** | {metrics['Valeur Stock']} | 💰 |
| **Catégories** | {metrics['Catégories']} | ✅ |
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
{i}. {priority_emoji} **{action['type'].upper()}** - {action['action']}
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

*Rapport généré par Retail-Heros sur Render*
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

# Interface Gradio
def create_app():
    with gr.Blocks(
        title="Retail-Heros - Analyse Rayon",
        theme=gr.themes.Soft(),
        css="""
            .gradio-container {max-width: 1200px !important; margin: auto;}
            .report-box {background: #f8f9fa; padding: 20px; border-radius: 10px; max-height: 400px; overflow-y: auto;}
        """
    ) as demo:
        
        gr.Markdown("""
        # 🏪 Retail-Heros - Analyse de Rayons
        ### Version Render - Optimisée pour performance
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                input_image = gr.Image(
                    label="📸 Upload une photo",
                    type="numpy",
                    sources=["upload"],
                    height=400
                )
                analyze_btn = gr.Button("🚀 Analyser", variant="primary", size="lg")
                status = gr.Textbox(label="Statut", interactive=False, value="Prêt")
            
            with gr.Column(scale=1):
                output_image = gr.Image(
                    label="🖼️ Résultat",
                    type="numpy",
                    height=400
                )
        
        with gr.Row():
            with gr.Column(scale=1):
                report = gr.Markdown("📋 **Rapport**", elem_classes="report-box")
            
            with gr.Column(scale=2):
                dashboard_output = gr.Plot(label="📊 Dashboard")
        
        analyze_btn.click(
            fn=process_shelf_image,
            inputs=input_image,
            outputs=[output_image, dashboard_output, report, status, gr.JSON(label="Métriques")]
        )
    
    return demo

if __name__ == "__main__":
    demo = create_app()
    demo.launch(
        server_name="0.0.0.0",
        server_port=10000,
        share=False
    )
