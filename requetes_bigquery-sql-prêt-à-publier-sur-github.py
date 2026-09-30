-- =====================================================================
-- PROJET    : Saisonnalité des passages aux urgences en France (2017-2023)
-- PIPELINE   : BigQuery → 6 CSV agrégés → Power BI Desktop
-- SOURCE     : DREES — passages quotidiens aux urgences par département
-- VUE SOURCE : mon-projet.drees_urgences_2017_2023.v_passages
--
-- NB PUBLICATION : l'identifiant de projet réel a été remplacé par
-- `mon-projet` — à conserver ainsi dans le dépôt public.
--
-- SORTIES : chaque requête correspond à un CSV du dossier data/ du dépôt.
-- =====================================================================


-- =====================================================================
-- REQUÊTE 1 — Série mensuelle nationale
-- → series_mensuelles_nationales.csv
-- BUT : la courbe nationale 2017-2023, avec la période COVID marquée
-- pour être distinguée à l'affichage dans Power BI (légende du visuel
-- « Série nationale »).
-- NOTE : periode et groupe_annees sont constantes pour toutes les dates
-- d'un même mois ; MAX() sert uniquement à satisfaire le GROUP BY —
-- aucun agrégat réel n'est calculé sur ces colonnes.
-- =====================================================================
SELECT
  DATE_TRUNC(date, MONTH)      AS mois,
  ROUND(SUM(nb_passages), 1)   AS passages_mois,
  MAX(periode)                 AS periode,
  MAX(groupe_annees)           AS groupe_annees
FROM `mon-projet.drees_urgences_2017_2023.v_passages`
GROUP BY mois
ORDER BY mois;


-- =====================================================================
-- REQUÊTE 2 — Indice de saisonnalité par groupe d'années
-- → ratio_mensuel_par_groupe.csv
-- BUT : rendre les mois comparables entre eux : 1 = moyenne annuelle
-- du groupe, > 1 = surcroît de passages, < 1 = creux. C'est cet indice
-- qui révèle le double pic juin-décembre et le renforcement post-COVID.
-- ÉTAPE 1 (quotidien) : agrégation nationale par jour — la moyenne PAR
-- JOUR neutralise la longueur inégale des mois (février vs juillet).
-- ÉTAPE 2 (par_mois) : moyenne par jour de chaque mois calendaire,
-- période COVID exclue (WHERE periode = 'comparable').
-- ÉTAPE 3 : division par la moyenne annuelle via AVG() OVER (PARTITION
-- BY groupe_annees) — fonction de fenêtre : chaque mois est comparé à
-- la moyenne des 12 mois de son groupe, sans perdre le détail par ligne.
-- LIMITES : l'annualisation approche la moyenne annuelle par la moyenne
-- des 12 moyennes mensuelles (exacte à faible écart près) — suffisant
-- pour un indice arrondi à 3 décimales.
-- =====================================================================
WITH quotidien AS (
  SELECT date, groupe_annees, periode, SUM(nb_passages) AS passages
  FROM `mon-projet.drees_urgences_2017_2023.v_passages`
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


-- =====================================================================
-- REQUÊTE 3 — Cycle mensuel brut par groupe
-- → cycle_mensuel_par_groupe.csv
-- BUT : la même moyenne par jour et par mois, SANS l'indice —
-- table de contrôle de la requête 2 (redondance volontaire :
-- permet de vérifier dans Power BI que l'indice est cohérent
-- avec les valeurs brutes qui l'ont produit).
-- =====================================================================
WITH quotidien AS (
  SELECT date, groupe_annees, periode, SUM(nb_passages) AS passages
  FROM `mon-projet.drees_urgences_2017_2023.v_passages`
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


-- =====================================================================
-- REQUÊTE 4 — Passages par jour de semaine
-- → passages_par_jour_semaine.csv
-- BUT : tester l'hypothèse 4 (surcharge du lundi, résultat publié par
-- la DREES — sa reproduction valide la méthodologie du projet).
-- NOTE : jour_semaine (0 = lundi ... 6 = dimanche) est déjà dérivé dans
-- la vue source ; le recodage depuis DAYOFWEEK (qui compte à partir du
-- dimanche) a été fait en amont dans v_passages.
-- passages_millions : somme nationale ramenée en millions pour lisibilité.
-- =====================================================================
SELECT jour_semaine,
       ROUND(SUM(nb_passages) / 1000000, 3) AS passages_millions
FROM `mon-projet.drees_urgences_2017_2023.v_passages`
GROUP BY jour_semaine
ORDER BY jour_semaine;


-- =====================================================================
-- REQUÊTE 5 — Passages par département et jour de semaine
-- → passages_par_dep_jour_semaine.csv
-- BUT : dimension territoriale du dashboard — croiser l'effet jour de
-- semaine avec le département (visualisation et filtres Power BI).
-- libelle_dep est déjà porté par la vue source (jointure amont).
-- =====================================================================
SELECT dep, libelle_dep, jour_semaine, ROUND(SUM(nb_passages), 1) AS passages
FROM `mon-projet.drees_urgences_2017_2023.v_passages`
GROUP BY dep, libelle_dep, jour_semaine;


-- =====================================================================
-- REQUÊTE 6 — Concentration estivale : top 20 des départements
-- → concentration_estivale_top_20.csv
-- BUT : tester l'hypothèse 2 — le tourisme d'été concentre-t-il les
-- passages dans certains départements, et la concentration s'accentue-
-- t-elle (2022-2023 vs 2017-2019) ?
-- ÉTAPE 1 (mensuel) : passages agrégés par département × mois.
-- ÉTAPE 2 (parts) : part des passages de juillet-août dans le total
-- annuel du groupe — IF(mois IN (7,8), ...) est une agrégation
-- conditionnelle : on ne somme que l'été au numérateur.
-- ÉTAPE 3 (pivot) : MAX(IF(groupe_annees = ...)) fait pivoter les deux
-- groupes en colonnes (une ligne par département) — c'est le point
-- d'entrée du CSV pour Power BI.
-- HAVING : ne garder que les départements présents dans les DEUX
-- groupes (sinon l'évolution serait incalculable).
-- =====================================================================
WITH mensuel AS (
  SELECT
    dep, libelle_dep, groupe_annees, periode,
    EXTRACT(MONTH FROM date) AS mois,
    SUM(nb_passages)         AS passages_mois
  FROM `mon-projet.drees_urgences_2017_2023.v_passages`
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