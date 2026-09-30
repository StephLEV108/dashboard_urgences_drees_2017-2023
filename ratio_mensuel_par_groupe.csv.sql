WITH quotidien AS (
  SELECT date, groupe_annees, periode, SUM(nb_passages) AS passages
  FROM `project-5dfecab1-2544-46d0-9cb.drees_urgences_2017_2023.v_passages`
  GROUP BY date, groupe_annees, periode
),
par_mois AS (
  SELECT
    EXTRACT(MONTH FROM date) AS mois,
    groupe_annees,
    AVG(passages)            AS moy_mois
  FROM quotidien
  WHERE periode = 'comparable'
  GROUP BY mois, groupe_annees
)
SELECT
  mois,
  groupe_annees,
  ROUND(moy_mois, 0) AS passages_moyens_par_jour,
  ROUND(moy_mois / AVG(moy_mois) OVER (PARTITION BY groupe_annees), 3)
                     AS ratio_vs_moyenne_annuelle
FROM par_mois
ORDER BY groupe_annees, mois;