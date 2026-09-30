SELECT jour_semaine,
       ROUND(SUM(nb_passages) / 1000000, 3) AS passages_millions
FROM `project-5dfecab1-2544-46d0-9cb.drees_urgences_2017_2023.v_passages`
GROUP BY jour_semaine
ORDER BY jour_semaine;