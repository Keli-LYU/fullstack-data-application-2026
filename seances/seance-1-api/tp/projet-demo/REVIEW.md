| Point de contrôle | OK / KO | Ce que j'ai corrigé |
|---|---|---|
| Les codes de statut correspondent à la spec (201, 404, 409) | ko|Limit the size of 'tarif' to avoid 500 errors. |
| `response_model` présent sur les 4 routes |ok| |
| La validation `date_fin > date_debut` est bien dans le schéma Pydantic |ok | |
| Le router n'accède pas au stockage de `items` | ok| |
| Pas d'`async def` sans `await` |ok| |
| Aucune dépendance ajoutée dans `requirements.txt` (ou justifiée) |ok | |
| Les routes littérales sont déclarées avant les routes paramétrées | ok| |
| Le code renvoie une réponse cohérente pour `POST /reservations/999/annuler` | ok| |