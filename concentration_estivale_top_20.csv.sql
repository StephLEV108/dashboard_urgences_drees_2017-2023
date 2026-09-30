WITH mensuel AS (
  SELECT
    dep, libelle_dep, groupe_annees, periode,
    EXTRACT(MONTH FROM date) AS mois,
    SUM(nb_passages)         AS passages_mois
  FROM `project-5dfecab1-2544-46d0-9cb.drees_urgences_2017_2023.v_passages`
  GROUP BY dep, libelle_dep, groupe_annees, periode, mois
),
parts AS (
  SELECT
    dep, libelle_dep, groupe_annees,
    SUM(IF(mois IN (7, 8), passages_mois, 0)) / SUM(passages_mois)
      AS part_estivale
  FROM mensuel
  WHERE periode = 'comparable'
  GROUP BY dep, libelle_dep, groupe_annees
)
SELECT
  dep,
  libelle_dep,
  ROUND(MAX(IF(groupe_annees = '2017-2019', part_estivale, NULL)), 4)
      AS part_ete_2017_2019,
  ROUND(MAX(IF(groupe_annees = '2022-2023', part_estivale, NULL)), 4)
      AS part_ete_2022_2023,
  ROUND(MAX(IF(groupe_annees = '2022-2023', part_estivale, NULL))
      - MAX(IF(groupe_annees = '2017-2019', part_estivale, NULL)), 4)
      AS evolution_part_ete
FROM parts
GROUP BY dep, libelle_dep
HAVING part_ete_2017_2019 IS NOT NULL AND part_ete_2022_2023 IS NOT NULL
ORDER BY part_ete_2022_2023 DESC
LIMIT 20;