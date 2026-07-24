import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

class RetailDashboard:
    @staticmethod
    def create_dashboard(analysis_data):
        """Crée un dashboard complet avec toutes les métriques"""
        
        if not analysis_data or not analysis_data.get('detections'):
            return RetailDashboard.create_empty_dashboard()
        
        # Créer la figure avec subplots
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                '📊 Distribution par Catégorie',
                '🏷️ Top Marques',
                '📈 Taux de Remplissage',
                '💰 Valeur du Stock',
                '📦 Part de Linéaire (Share of Shelf)',
                '🎯 Conformité Planogramme'
            ),
            specs=[
                [{'type': 'pie'}, {'type': 'bar'}],
                [{'type': 'indicator'}, {'type': 'indicator'}],
                [{'type': 'bar'}, {'type': 'indicator'}]
            ]
        )
        
        # 1. Graphique catégories
        categories = analysis_data.get('categories', {})
        if categories:
            fig.add_trace(
                go.Pie(
                    labels=list(categories.keys()),
                    values=list(categories.values()),
                    hole=0.3,
                    marker=dict(colors=px.colors.qualitative.Set3)
                ),
                row=1, col=1
            )
        
        # 2. Top marques
        brands = analysis_data.get('brands', {})
        if brands:
            sorted_brands = sorted(brands.items(), key=lambda x: x[1], reverse=True)[:5]
            fig.add_trace(
                go.Bar(
                    x=[b[0] for b in sorted_brands],
                    y=[b[1] for b in sorted_brands],
                    marker_color='lightblue',
                    text=[b[1] for b in sorted_brands],
                    textposition='auto'
                ),
                row=1, col=2
            )
        
        # 3. Taux de remplissage
        fill_rate = analysis_data.get('fill_rate', 0)
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=fill_rate,
                title={'text': "Taux de Remplissage"},
                domain={'row': 0, 'column': 0},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "darkgreen"},
                    'steps': [
                        {'range': [0, 50], 'color': "red"},
                        {'range': [50, 75], 'color': "orange"},
                        {'range': [75, 100], 'color': "green"}
                    ]
                }
            ),
            row=2, col=1
        )
        
        # 4. Valeur estimée
        estimated_value = analysis_data.get('estimated_value', 0)
        fig.add_trace(
            go.Indicator(
                mode="number+delta",
                value=estimated_value,
                title={'text': "Valeur du Stock (€)"},
                delta={'reference': 400, 'relative': True},
                domain={'row': 0, 'column': 0}
            ),
            row=2, col=2
        )
        
        # 5. Part de linéaire (Share of Shelf)
        share_of_shelf = analysis_data.get('facing_analysis', {}).get('share_of_shelf', {})
        if share_of_shelf:
            sorted_products = sorted(share_of_shelf.items(), key=lambda x: x[1], reverse=True)[:5]
            fig.add_trace(
                go.Bar(
                    x=[p[0] for p in sorted_products],
                    y=[p[1] for p in sorted_products],
                    marker_color='lightgreen',
                    name='Share of Shelf'
                ),
                row=3, col=1
            )
        
        # 6. Conformité planogramme
        compliance = analysis_data.get('planogram_compliance', 0)
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=compliance,
                title={'text': "Conformité Planogramme"},
                domain={'row': 0, 'column': 0},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "red"},
                        {'range': [50, 70], 'color': "orange"},
                        {'range': [70, 100], 'color': "green"}
                    ]
                }
            ),
            row=3, col=2
        )
        
        fig.update_layout(
            height=800,
            showlegend=True,
            title_text="📊 Dashboard Retail-Heros - Analyse Complète",
            title_font_size=24,
            template='plotly_white'
        )
        
        return fig
    
    @staticmethod
    def create_empty_dashboard():
        """Dashboard vide"""
        fig = go.Figure()
        fig.add_annotation(
            text="Aucune donnée à afficher.<br>📸 Upload une image pour l'analyse !",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=24, color="gray")
        )
        fig.update_layout(
            height=500,
            xaxis=dict(showgrid=False, zeroline=False, visible=False),
            yaxis=dict(showgrid=False, zeroline=False, visible=False)
        )
        return fig
    
    @staticmethod
    def create_performance_metrics(analysis_data):
        """Crée un tableau de métriques détaillées"""
        if not analysis_data:
            return {
                'Total Produits': 0,
                'Produits Uniques': 0,
                'Taux Remplissage': '0%',
                'Conformité Planogramme': '0%',
                'Valeur Stock': '0€',
                'Catégories': 0,
                'Total Facings': 0,
                'Ruptures': 0
            }
        
        return {
            'Total Produits': analysis_data.get('total_products', 0),
            'Produits Uniques': analysis_data.get('unique_products', 0),
            'Taux Remplissage': f"{analysis_data.get('fill_rate', 0):.1f}%",
            'Conformité Planogramme': f"{analysis_data.get('planogram_compliance', 0):.1f}%",
            'Valeur Stock': f"{analysis_data.get('estimated_value', 0):.2f}€",
            'Catégories': len(analysis_data.get('categories', {})),
            'Total Facings': analysis_data.get('facing_analysis', {}).get('total_facings', 0),
            'Ruptures': len(analysis_data.get('detected_gaps', []))
        }