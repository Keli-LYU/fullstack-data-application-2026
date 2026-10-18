| État | Nœud observé | Lignes retournées | Execution Time |
|---|---|---:|---:|
| Sans index sur titre | Seq Scan | 1 | 6.824 ms |
| Avec idx_items_titre | Index Scan | 1 | 0.050 ms |

## (a) Joker en tête : recherche par suffixe

Résultat : Seq Scan, 9.979 ms, 1 ligne retournée.

Explication : le joker initial ne fixe aucun préfixe, donc le B-tree trié par
le début du titre ne peut pas délimiter une plage utile et le plan parcourt la table.

## (b) Index sur disponible

| Condition | Nœud observé | Lignes retournées | Execution Time |
|---|---|---:|---:|
| disponible = TRUE | Seq Scan | 200 004 | 13.445 ms |
| disponible = FALSE | Index Scan using idx_items_disponible | 0 | 0.028 ms |

TRUE : comme toutes les lignes correspondent, une lecture séquentielle évite
le coût supplémentaire de parcourir l'index puis de récupérer toute la table.

FALSE : l'index permet de constater rapidement l'absence de cette valeur sans
parcourir les 200 004 lignes.