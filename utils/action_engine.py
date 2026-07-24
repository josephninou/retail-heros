class ActionEngine:
    def __init__(self):
        self.thresholds = {
            'min_sos': 10,  # Part de linéaire minimum
            'max_gaps': 3,   # Nombre max de gaps acceptables
            'min_fill_rate': 80,  # Taux de remplissage minimum
            'min_compliance': 70  # Conformité planogramme minimum
        }
    
    def generate_actions(self, analysis_data):
        """
        Génère des actions recommandées basées sur l'analyse
        """
        actions = []
        
        # 1. Analyse du Share of Shelf
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
        
        # 2. Analyse des gaps (ruptures)
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
        
        # 3. Analyse du taux de remplissage
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
        
        # 4. Analyse de la conformité planogramme
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
        
        # 5. Recommandations de prix
        estimated_value = analysis_data.get('estimated_value', 0)
        if estimated_value < 100:
            actions.append({
                'type': 'pricing',
                'product': 'Tous',
                'action': "💡 Valeur de stock faible. Considérer une promotion pour stimuler les ventes.",
                'priority': 'low',
                'impact': 'medium',
                'category': 'Pricing'
            })
        
        # Trier par priorité
        priority_order = {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}
        actions.sort(key=lambda x: priority_order.get(x.get('priority', 'low'), 4))
        
        return actions
    
    def get_priority_summary(self, actions):
        """Résumé des priorités"""
        summary = {'urgent': 0, 'high': 0, 'medium': 0, 'low': 0}
        for action in actions:
            priority = action.get('priority', 'low')
            summary[priority] = summary.get(priority, 0) + 1
        return summary
