SELECT dep, libelle_dep, jour_semaine, ROUND(SUM(nb_passages), 1) AS passages
FROM `project-5dfecab1-2544-46d0-9cb.drees_urgences_2017_2023.v_passages`
GROUP BY dep, libelle_dep, jour_semaine;