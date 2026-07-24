import plotly.graph_objects as go

class RetailDashboard:
    @staticmethod
    def create_dashboard(analysis_data):
        fig = go.Figure()
        fig.add_annotation(
            text="📊 Dashboard Retail-Heros",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=24, color="#2c3e50")
        )
        fig.update_layout(height=400)
        return fig
