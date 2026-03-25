import { Router } from 'express';

const router = Router();

const RECOMMENDATIONS = [
  {
    id: 1, priority: 'critique', pilier: 'Réputation',
    titre: 'Communiqué de crise vélo — 48h max',
    description: '1 500+ mentions négatives en 15 jours sur l\'accident vélo défectueux. Pic observé 7-10 mars. Publier un communiqué transparent avec plan de rappel et ouvrir une hotline dédiée dans les 48h pour stopper la propagation.',
    impact: 'Réduction estimée de 60% du volume négatif en 7 jours',
    effort: 'Faible', kpi_cible: 'Gravity Score < 4 sous 2 semaines',
  },
  {
    id: 2, priority: 'haute', pilier: 'CX',
    titre: 'Chatbot SAV première réponse',
    description: '40% des avis négatifs portent sur le SAV (injoignable, délais). Un chatbot de triage et première réponse automatique pourrait absorber 60% des cas simples (suivi commande, politique retour, disponibilité).',
    impact: 'Réduction de 40% des avis 1-2★ liés au SAV en 3 mois',
    effort: 'Moyen', kpi_cible: 'NPS proxy +15 pts en Q3 2026',
  },
  {
    id: 3, priority: 'haute', pilier: 'Benchmark',
    titre: 'Renforcer le positionnement qualité/prix vs Intersport',
    description: 'Decathlon conserve +45% de Share of Voice sur le rapport qualité/prix. Intersport gagne sur les grandes marques (935 magasins vs 335). Ne pas engager le combat sur les marques premium — capitaliser sur l\'accessibilité et les marques propres.',
    impact: 'Maintien du lead qualité/prix, éviter la dilution brand',
    effort: 'Stratégique', kpi_cible: 'SOV Decathlon > 60% sur topic Prix',
  },
  {
    id: 4, priority: 'moyenne', pilier: 'CX',
    titre: 'Programme fidélité axé sur les enchantements identifiés',
    description: 'Les enchantements les plus cités sont : rapport qualité/prix, conseil vendeur et choix du rayon. Amplifier ces points forts via un programme de récompenses ciblé et des campagnes UGC (contenus générés par les clients satisfaits).',
    impact: 'Augmentation du taux de recommandation organique',
    effort: 'Moyen', kpi_cible: 'Score enchantement +20% en 6 mois',
  },
];

router.get('/recommendations', (req, res) => {
  res.json({ recommendations: RECOMMENDATIONS });
});

export default router;
