import plotly.graph_objects as go
from plotly.subplots import make_subplots

class RetailDashboard:
    @staticmethod
    def create_dashboard(analysis_data):
        if not analysis_data or not analysis_data.get('detections'):
            fig = go.Figure()
            fig.add_annotation(
                text="📸 Upload une image pour voir le dashboard",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=20, color="gray")
            )
            fig.update_layout(height=500)
            return fig

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("📊 Catégories", "🏷️ Marques", "📈 Taux de remplissage", "💰 Valeur du stock")
        )

        categories = analysis_data.get('categories', {})
        if categories:
            fig.add_trace(
                go.Pie(labels=list(categories.keys()), values=list(categories.values()), hole=0.3),
                row=1, col=1
            )

        brands = analysis_data.get('brands', {})
        if brands:
            sorted_brands = sorted(brands.items(), key=lambda x: x[1], reverse=True)[:5]
            fig.add_trace(
                go.Bar(x=[b[0] for b in sorted_brands], y=[b[1] for b in sorted_brands], marker_color='lightblue'),
                row=1, col=2
            )

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

        estimated_value = analysis_data.get('estimated_value', 0)
        fig.add_trace(
            go.Indicator(mode="number", value=estimated_value, title={'text': "Valeur (€)"}),
            row=2, col=2
        )

        fig.update_layout(height=550, showlegend=False)
        return fig
