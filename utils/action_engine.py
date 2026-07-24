class ActionEngine:
    def __init__(self):
        self.thresholds = {
            'min_sos': 10,
            'max_gaps': 3,
            'min_fill_rate': 80,
            'min_compliance': 70
        }
    
    def generate_actions(self, analysis_data):
        actions = []
        
        share_of_shelf = analysis_data.get('facing_analysis', {}).get('share_of_shelf', {})
        for product, sos in share_of_shelf.items():
            if sos < self.thresholds['min_sos']:
                actions.append({
                    'type': 'share_of_shelf',
                    'product': product,
                    'action': f"📊 Augmenter les facings de '{product}'. Part de linéaire actuelle: {sos:.1f}% (minimum recommandé: {self.thresholds['min_sos']}%)",
                    'priority': 'high',
                    'impact': 'medium',
                    'category': 'Merchandising'
                })
        
        gaps = analysis_data.get('detected_gaps', [])
        if gaps:
            for gap in gaps:
                priority = 'urgent' if gap.get('severity') == 'high' else 'high'
                actions.append({
                    'type': 'stock_gap',
                    'product': gap.get('expected_product', 'Inconnu'),
                    'action': f"🔴 Rupture de stock détectée. Produit: {gap.get('expected_product', 'Inconnu')}. Réassortir immédiatement.",
                    'priority': priority,
                    'impact': 'high',
                    'category': 'Stock'
                })
        
        fill_rate = analysis_data.get('fill_rate', 0)
        if fill_rate < self.thresholds['min_fill_rate']:
            actions.append({
                'type': 'fill_rate',
                'product': 'Tous',
                'action': f"⚠️ Taux de remplissage faible: {fill_rate}%. Optimiser l'approvisionnement des produits les plus vendus.",
                'priority': 'high',
                'impact': 'high',
                'category': 'Stock'
            })
        
        compliance = analysis_data.get('planogram_compliance', 0)
        if compliance < self.thresholds['min_compliance']:
            actions.append({
                'type': 'planogram',
                'product': 'Tous',
                'action': f"🔄 Non-conformité planogramme: {compliance}%. Réorganiser le rayon selon le plan défini.",
                'priority': 'medium',
                'impact': 'medium',
                'category': 'Merchandising'
            })
        
        priority_order = {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}
        actions.sort(key=lambda x: priority_order.get(x.get('priority', 'low'), 4))
        
        return actions
