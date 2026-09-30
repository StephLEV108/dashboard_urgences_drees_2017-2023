WITH quotidien AS (
  SELECT date, groupe_annees, periode, SUM(nb_passages) AS passages
  FROM `project-5dfecab1-2544-46d0-9cb.drees_urgences_2017_2023.v_passages`
  GROUP BY date, groupe_annees, periode
)
SELECT
  EXTRACT(MONTH FROM date) AS mois,
  groupe_annees,
  ROUND(AVG(passages))     AS passages_moyens_par_jour
FROM quotidien
WHERE periode = 'comparable'
GROUP BY mois, groupe_annees
ORDER BY groupe_annees, mois;