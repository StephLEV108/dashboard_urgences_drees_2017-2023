SELECT
  DATE_TRUNC(date, MONTH)     AS mois,
  ROUND(SUM(nb_passages), 1)  AS passages_mois,
  MAX(periode)                AS periode,
  MAX(groupe_annees)          AS groupe_annees
FROM `project-5dfecab1-2544-46d0-9cb.drees_urgences_2017_2023.v_passages`
GROUP BY mois
ORDER BY mois;