# Projet démo — TP séance 2

Ce dossier est le point de départ du [TP de la séance 2](../README.md). Il contient l'API en
mémoire **telle que je l'attendais à la fin du TP de la séance 1** : le CRUD complet sur `items`,
la ressource `reservations` telle que spécifiée en séance 1, le découpage en routers et la
validation croisée des dates dans le schéma Pydantic.

Vous travaillez normalement sur **votre** API de la séance 1. Ce projet sert de secours si votre
rendu n'est pas terminé ou n'est pas conforme, et de référence pour comparer : si un test du TP 2
échoue chez vous et passe ici, la différence est dans votre code, pas dans le test.

Les tests de contrat et les tests unitaires sont dans `tests/`. Les routers et schémas sont
repris du projet de la séance 1 ; `/health` conserve le contrat de cette séance. Les identifiants
sont calculés à partir du stockage, qui est vidé avant et après chaque test.

## Arborescence

```text
projet-demo/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── items.py
│   │   └── reservations.py
│   └── schemas/
│       ├── __init__.py
│       ├── item.py
│       └── reservation.py
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Démarrer

Depuis ce dossier :

```bash
docker compose up --build
```

L'API répond sur [http://localhost:8000/health](http://localhost:8000/health) et sa documentation
interactive est disponible sur [http://localhost:8000/docs](http://localhost:8000/docs), avec les
deux ressources `items` et `reservations`.

Le montage de volume et `--reload` sont réservés au développement : le code est rechargé à chaque
sauvegarde sans reconstruction de l'image. `tests/` et `pytest.ini` sont copiés dans l'image et montés dans le conteneur de développement.

## Lancer les tests

Depuis `projet-demo/`, dans le conteneur :

```bash
docker compose build api
docker compose run --rm api pytest -v
docker compose run --rm api pytest --cov=app --cov-branch --cov-report=term-missing
```

Ou localement sous PowerShell :

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -v
.\.venv\Scripts\python.exe -m pytest --cov=app --cov-branch --cov-report=term-missing
```

- `tests/conftest.py` : fixtures `storage`, `client`, `item_velo`, `reservation_active`.
- `tests/test_health.py` : contrat de santé.
- `tests/test_items.py` : CRUD, validation, champs inconnus, filtres, pagination et absence d'effets de bord après rejet.
- `tests/test_reservations.py` : création, lecture, filtre, limite, dates, annulation, erreurs 404 et conflit 409.
- `tests/test_schemas.py` : validation croisée des dates et distinction entre champ absent et `description=null`.

Les tests utilisent `TestClient`, sans serveur HTTP. Le stockage réel est remis à zéro pour chaque test.
Conformément au contrat de la séance 1, une réservation ne vérifie pas l'existence de l'item.
