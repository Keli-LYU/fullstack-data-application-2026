-- Étape 3 : requêtes testées sur les données de 02-seed.sql.

-- 1. Items disponibles à moins de 10 €/jour, par tarif croissant.
SELECT id, titre, tarif_jour
FROM items
WHERE disponible = true AND tarif_jour < 10
ORDER BY tarif_jour ASC, id ASC;
-- Résultat :
-- id | titre         | tarif_jour
--  2 | Perceuse      | 5.00
--  1 | Vélo de ville | 8.50

-- 2. Titre contenant « velo », sans tenir compte de la casse.
SELECT id, titre
FROM items
WHERE titre ILIKE '%velo%'
ORDER BY id;
-- Résultat : 0 ligne.
-- ILIKE ignore la casse, mais ici ne supprime pas les accents :
-- « velo » ne correspond donc pas à « Vélo de ville ».

-- 3. Chaque item et le nom de son propriétaire.
SELECT i.id, i.titre, u.display_name AS proprietaire
FROM items AS i
JOIN users AS u ON u.id = i.owner_id
ORDER BY i.id;
-- Résultat :
-- id | titre          | proprietaire
--  1 | Vélo de ville  | Alice
--  2 | Perceuse       | Alice
--  3 | Tente 2 places | Bob
--  4 | Appareil photo | Bob

-- 4. Nombre de réservations par item, même sans réservation.
SELECT i.id, i.titre, COUNT(r.id) AS nombre_reservations
FROM items AS i
LEFT JOIN reservations AS r ON r.item_id = i.id
GROUP BY i.id, i.titre
ORDER BY i.id;
-- Résultat :
-- id | titre          | nombre_reservations
--  1 | Vélo de ville  | 1
--  2 | Perceuse       | 0
--  3 | Tente 2 places | 1
--  4 | Appareil photo | 1
-- LEFT JOIN conserve les items jamais réservés.
-- Pour la Perceuse, r.id vaut NULL : COUNT(r.id) donne 0.
-- COUNT(*) compterait la ligne du LEFT JOIN et donnerait à tort 1.

-- 5. Utilisateurs ayant publié au moins un item : nombre et tarif moyen.
SELECT u.display_name,
       COUNT(i.id) AS nombre_items,
       ROUND(AVG(i.tarif_jour), 2) AS tarif_moyen
FROM users AS u
JOIN items AS i ON i.owner_id = u.id
GROUP BY u.id, u.display_name
ORDER BY u.id;
-- Résultat :
-- display_name | nombre_items | tarif_moyen
-- Alice        | 2            | 6.75
-- Bob          | 2            | 16.00
-- La jointure interne exclut Chloé, qui n'a publié aucun item.

-- 6. Réservations actives commençant après le 1er septembre 2026.
SELECT r.id, i.titre, u.display_name AS emprunteur,
       r.date_debut, r.date_fin
FROM reservations AS r
JOIN items AS i ON i.id = r.item_id
JOIN users AS u ON u.id = r.borrower_id
WHERE r.statut = 'active' AND r.date_debut > DATE '2026-09-01'
ORDER BY r.id;
-- Résultat :
-- id | titre          | emprunteur | date_debut | date_fin
--  2 | Tente 2 places | Alice      | 2026-09-10 | 2026-09-12
--  3 | Appareil photo | Chloé      | 2026-09-15 | 2026-09-20

-- 7. Deux items après avoir sauté le premier dans l'ordre des tarifs décroissants.
SELECT id, titre, tarif_jour
FROM items
ORDER BY tarif_jour DESC, id ASC
LIMIT 2 OFFSET 1;
-- Résultat :
-- id | titre          | tarif_jour
--  3 | Tente 2 places | 12.00
--  1 | Vélo de ville  | 8.50
-- L'Appareil photo (20.00) est sauté. L'id départage les tarifs égaux.

-- 8. Chiffre d'affaires potentiel de chaque réservation active.
SELECT r.id, i.titre, i.tarif_jour,
       r.date_fin - r.date_debut AS nombre_jours,
       i.tarif_jour * (r.date_fin - r.date_debut) AS chiffre_affaires_potentiel
FROM reservations AS r
JOIN items AS i ON i.id = r.item_id
WHERE r.statut = 'active'
ORDER BY r.id;
-- Résultat :
-- id | titre          | tarif_jour | nombre_jours | chiffre_affaires_potentiel
--  2 | Tente 2 places | 12.00      | 2            | 24.00
--  3 | Appareil photo | 20.00      | 5            | 100.00
