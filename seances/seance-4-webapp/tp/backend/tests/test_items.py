import pytest
from fastapi.testclient import TestClient


def test_creer_item_et_le_relire(client: TestClient):
    payload = {'titre': 'Vélo de ville', 'tarif_jour': 8.5}
    response = client.post('/items', json=payload)
    assert response.status_code == 201
    item = response.json()
    assert item == {'id': 1, **payload, 'description': None, 'disponible': True}
    lecture = client.get(f"/items/{item['id']}")
    assert lecture.status_code == 200
    assert lecture.json() == item
    second = client.post('/items', json=payload)
    assert second.status_code == 201
    assert second.json()['id'] != item['id']


def test_liste_initialement_vide(client):
    response = client.get('/items')
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize(('changement', 'champ'), [
    ({'titre': 'ab'}, 'titre'), ({'titre': 'x' * 121}, 'titre'),
    ({'description': 'x' * 1001}, 'description'),
    ({'tarif_jour': 0}, 'tarif_jour'), ({'tarif_jour': -3}, 'tarif_jour'),
    ({'couleur': 'rouge'}, 'couleur'),
])
def test_creation_invalide_renvoie_422(client, changement, champ):
    payload = {'titre': 'Vélo de ville', 'tarif_jour': 8.5, **changement}
    response = client.post('/items', json=payload)
    assert response.status_code == 422
    assert champ in [error['loc'][-1] for error in response.json()['detail']]
    assert client.get('/items').json() == []


@pytest.mark.parametrize('payload', [{}, {'titre': 'Vélo'}, {'tarif_jour': 8.5}])
def test_creation_champ_obligatoire_manquant(client, payload):
    assert client.post('/items', json=payload).status_code == 422


@pytest.mark.parametrize('longueur', [3, 120])
def test_creation_bornes_valides(client, longueur):
    response = client.post('/items', json={
        'titre': 'x' * longueur, 'description': 'x' * 1000, 'tarif_jour': 0.01,
    })
    assert response.status_code == 201
    assert response.json()['titre'] == 'x' * longueur


def test_put_remplace_et_reinitialise_les_champs_optionnels(client, item_velo):
    path = f"/items/{item_velo['id']}"
    assert client.patch(path, json={'disponible': False}).status_code == 200
    response = client.put(path, json={'titre': 'Tente', 'tarif_jour': 12})
    assert response.status_code == 200
    assert response.json() == {
        'id': item_velo['id'], 'titre': 'Tente', 'tarif_jour': 12,
        'description': None, 'disponible': True,
    }
    assert client.get(path).json() == response.json()


@pytest.mark.parametrize('changes', [
    {'titre': 'Vélo pliant'}, {'tarif_jour': 10}, {'disponible': False},
    {'description': None}, {},
])
def test_patch_preserve_les_champs_non_fournis(client, item_velo, changes):
    path = f"/items/{item_velo['id']}"
    response = client.patch(path, json=changes)
    assert response.status_code == 200
    assert response.json() == {**item_velo, **changes}
    assert client.get(path).json() == response.json()


@pytest.mark.parametrize(('method', 'payload'), [
    ('put', {'titre': 'Tente'}), ('put', {'titre': 'Tente', 'tarif_jour': 0}),
    ('patch', {'titre': 'ab'}), ('patch', {'tarif_jour': -1}),
    ('patch', {'couleur': 'rouge'}),
])
def test_modification_invalide_ne_change_pas_item(client, item_velo, method, payload):
    path = f"/items/{item_velo['id']}"
    assert client.request(method, path, json=payload).status_code == 422
    assert client.get(path).json() == item_velo


def test_supprimer_item_et_verifier_absence(client, item_velo):
    path = f"/items/{item_velo['id']}"
    response = client.delete(path)
    assert response.status_code == 204
    assert response.content == b''
    assert client.get(path).status_code == 404
    assert client.delete(path).status_code == 404
    assert client.get('/items').json() == []


@pytest.mark.parametrize('method', ['get', 'put', 'patch', 'delete'])
def test_item_absent_renvoie_404(client, method):
    kwargs = {'json': {'titre': 'Tente', 'tarif_jour': 5}} if method in ('put', 'patch') else {}
    assert client.request(method, '/items/999', **kwargs).status_code == 404


@pytest.mark.parametrize('method', ['get', 'put', 'patch', 'delete'])
@pytest.mark.parametrize('item_id', ['abc', '0', '-1'])
def test_identifiant_item_invalide(client, method, item_id):
    kwargs = {'json': {'titre': 'Tente', 'tarif_jour': 5}} if method in ('put', 'patch') else {}
    assert client.request(method, f'/items/{item_id}', **kwargs).status_code == 422


@pytest.mark.parametrize('params', [
    {'skip': -1}, {'limit': 0}, {'limit': 101}, {'disponible': 'peut-etre'},
])
def test_parametres_liste_invalides(client, params):
    assert client.get('/items', params=params).status_code == 422


def test_filtres_et_pagination_appliques_dans_le_bon_ordre(client, storage):
    for i in range(1, 51):
        storage.items[i] = {
            'id': i, 'titre': f'Vélo {i}' if i % 2 else f'Tente {i}',
            'description': None, 'tarif_jour': 5, 'disponible': i % 3 == 0,
        }
    cases = [
        ({}, list(range(1, 21))),
        ({'skip': 40, 'limit': 20}, list(range(41, 51))),
        ({'skip': 50}, []), ({'limit': 100}, list(range(1, 51))),
        ({'q': 'VÉLO', 'skip': 1, 'limit': 2}, [3, 5]),
        ({'disponible': 'true', 'limit': 2}, [3, 6]),
        ({'disponible': 'false', 'limit': 2}, [1, 2]),
        ({'q': 'vélo', 'disponible': 'true', 'skip': 1, 'limit': 2}, [9, 15]),
        ({'q': 'introuvable'}, []),
    ]
    for params, expected in cases:
        response = client.get('/items', params=params)
        assert response.status_code == 200
        assert [item['id'] for item in response.json()] == expected
