# Ressource : reservations

## Périmètre et fichiers

Implémenter la ressource dans `app/schemas/reservation.py` et
`app/routers/reservations.py`, puis inclure son router dans `app/main.py`.
Conserver les opérations `items` et `/health` existantes.

Stockage : dictionnaire en mémoire propre au router, avec un compteur d'identifiants
commençant à 1. Le serveur attribue l'identifiant à la création ; le client ne le choisit pas.
Les données ne sont pas persistées après un redémarrage.

## Schémas

`ReservationCreate` :

- `item_id` : entier obligatoire, >= 1 ;
- `date_debut` : date obligatoire ;
- `date_fin` : date obligatoire, strictement postérieure à `date_debut` ;
- champs inconnus refusés (`extra="forbid"`).

Les clients transmettent les dates au format ISO `YYYY-MM-DD`.
Implémenter la comparaison des dates dans un `@model_validator(mode="after")`
Pydantic et lever une `ValueError` si `date_fin <= date_debut` : FastAPI doit
répondre `422`, sans insérer de réservation ni incrémenter le compteur.
Les dates passées ne sont pas interdites par ce contrat.

`ReservationRead` : `id` (entier), `item_id` (entier), `date_debut` (date),
`date_fin` (date), `statut` (`Literal["active", "annulee"]`).
Les dates sont renvoyées sous forme de chaînes ISO.

## Routes

Préfixe `/reservations`, tag `reservations`. Tous les paramètres de chemin
`reservation_id` sont des entiers >= 1 ; un format invalide produit `422`.

| Méthode | Chemin du router | Succès et modèle de réponse | Erreurs |
|---|---|---|---|
| POST | `""` | `201`, `ReservationRead`, statut initial `active` | `422` si corps invalide ou `date_fin <= date_debut` |
| GET | `""` | `200`, `list[ReservationRead]` | `422` si paramètres invalides |
| GET | `"/{reservation_id}"` | `200`, `ReservationRead` | `404` si absente |
| POST | `"/{reservation_id}/annuler"` | `200`, `ReservationRead`, statut `annulee` | `404` si absente ; `409` si déjà annulée |

Paramètres de la liste : `item_id` facultatif (entier >= 1), `limit` (défaut 20,
minimum 1, maximum 100). Filtrer par `item_id` avant d'appliquer la limite.
Sans résultat, renvoyer `[]` avec `200`. Les réservations annulées restent consultables
et figurent dans la liste ; l'annulation ne modifie ni l'item ni les dates.

Pour une réservation absente, utiliser le détail `Reservation {reservation_id} introuvable`.
Pour une seconde annulation, utiliser `Reservation {reservation_id} deja annulee`.
Le corps d'erreur utilise la clé `detail` de FastAPI.

## Contraintes d'implémentation

- Aucun accès au `FAKE_DB` du router `items`, ni vérification de l'existence de l'item.
  Une réservation avec `item_id=999` peut donc être créée même si cet item n'existe pas.
- `response_model` explicite sur les quatre routes ; ne pas exposer de champs internes.
- Valider les corps dans Pydantic et les paramètres avec `Path` / `Query`.
  Les `if` métier pour l'absence ou le statut déjà annulé restent dans le router.
- Utiliser `def` pour ces opérations en mémoire, sans `async def` dépourvu d'`await`.
- Déclarer les routes de collection avant les routes paramétrées.
- Ne pas ajouter de dépendance dans `requirements.txt`.
- Ne pas ajouter de contrôle de chevauchement, de disponibilité, d'authentification
  ou de base de données : ces fonctionnalités ne font pas partie de ce TP.

## Exemple et critères d'acceptation

Requête de création :

```json
{"item_id": 999, "date_debut": "2026-11-01", "date_fin": "2026-11-02"}
```

Sur un stockage vide, réponse `201` :

```json
{"id": 1, "item_id": 999, "date_debut": "2026-11-01", "date_fin": "2026-11-02", "statut": "active"}
```

Vérifier ensuite : lecture de `1` → `200` ; première annulation de `1` → `200`
et statut `annulee` ; seconde annulation → `409` ; annulation de `999` absent → `404`.
Avec des dates égales ou inversées → `422`. Avec `limit=101`, `item_id=0` ou un
identifiant de chemin non entier → `422`. La documentation `/docs` doit présenter
les quatre opérations sous le tag `reservations`.
