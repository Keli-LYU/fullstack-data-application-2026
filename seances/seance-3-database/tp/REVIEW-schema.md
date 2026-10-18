Je retiens la conservation de l'historique : fermer un compte ne doit effacer ni les prêts réalisés sur son matériel, ni ses propres emprunts. Les réservations actives doivent être traitées avant la fermeture du compte.

| Point de contrôle | OK / KO | Ce que j'ai corrigé |
|---|---|---|
| Chaque table a une clé primaire | | |
| Les clés étrangères sont déclarées avec `REFERENCES` |ok | |
| Les `ON DELETE` sont explicites et cohérents avec le métier |ok | |
| La règle « un seul avis par réservation » est garantie par une contrainte `UNIQUE` |ok | |
| La note est bornée par un `CHECK (note BETWEEN 1 AND 5)` | ok| |
| La table de liaison item/tag a une clé primaire composite | ok| |
| Le libellé de tag est `UNIQUE` | ok| |
| Les contraintes sont nommées | ok| |
| Des index existent sur les clés étrangères |ok | |
| Le non-chevauchement est réellement garanti (contrainte) ou explicitement laissé à l'applicatif | ok| |
| Aucun type flottant pour un montant, aucun `TIMESTAMP` sans fuseau |ok | |