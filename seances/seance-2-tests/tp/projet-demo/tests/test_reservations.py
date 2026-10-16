import pytest


PAYLOAD = {'item_id': 999, 'date_debut': '2026-09-01', 'date_fin': '2026-09-05'}


def test_creer_reservation_sans_acces_aux_items(client):
    # Session 1 explicitly keeps reservations independent of the items storage.
    response = client.post('/reservations', json=PAYLOAD)
    assert response.status_code == 201
    reservation = response.json()
    assert reservation == {'id': 1, **PAYLOAD, 'statut': 'active'}
    lecture = client.get(f"/reservations/{reservation['id']}")
    assert lecture.status_code == 200
    assert lecture.json() == reservation
    second = client.post('/reservations', json=PAYLOAD)
    assert second.status_code == 201
    assert second.json()['id'] != reservation['id']


def test_liste_reservations_initialement_vide(client):
    response = client.get('/reservations')
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize('changes', [
    {'date_fin': '2026-09-01'}, {'date_fin': '2026-08-31'},
    {'date_debut': 'invalide'}, {'date_fin': '2026-02-30'},
    {'item_id': 0}, {'item_id': -1},
])
def test_creation_reservation_invalide(client, changes):
    response = client.post('/reservations', json={**PAYLOAD, **changes})
    assert response.status_code == 422
    assert response.json()['detail']
    assert client.get('/reservations').json() == []


@pytest.mark.parametrize('field', ['item_id', 'date_debut', 'date_fin'])
def test_champ_reservation_obligatoire(client, field):
    payload = {key: value for key, value in PAYLOAD.items() if key != field}
    response = client.post('/reservations', json=payload)
    assert response.status_code == 422
    assert field in [error['loc'][-1] for error in response.json()['detail']]


def test_annuler_reservation_persiste_statut(client, reservation_active):
    path = f"/reservations/{reservation_active['id']}"
    response = client.post(f'{path}/annuler')
    assert response.status_code == 200
    assert response.json() == {**reservation_active, 'statut': 'annulee'}
    assert client.get(path).json() == response.json()
    assert client.get('/reservations').json() == [response.json()]


def test_annuler_deux_fois_renvoie_409(client, reservation_active):
    path = f"/reservations/{reservation_active['id']}"
    assert client.post(f'{path}/annuler').status_code == 200
    assert client.post(f'{path}/annuler').status_code == 409
    assert client.get(path).json() == {**reservation_active, 'statut': 'annulee'}


@pytest.mark.parametrize(('method', 'suffix'), [('get', ''), ('post', '/annuler')])
def test_reservation_absente_renvoie_404(client, method, suffix):
    assert client.request(method, f'/reservations/999{suffix}').status_code == 404


@pytest.mark.parametrize(('method', 'suffix'), [('get', ''), ('post', '/annuler')])
@pytest.mark.parametrize('reservation_id', ['abc', '0', '-1'])
def test_identifiant_reservation_invalide(client, method, suffix, reservation_id):
    assert client.request(method, f'/reservations/{reservation_id}{suffix}').status_code == 422


@pytest.mark.parametrize('params', [{'limit': 0}, {'limit': 101}, {'item_id': 0}])
def test_parametres_liste_reservations_invalides(client, params):
    assert client.get('/reservations', params=params).status_code == 422


def test_filtrer_reservations_avant_limite(client, storage):
    for i in range(1, 26):
        storage.reservations[i] = {
            'id': i, **PAYLOAD, 'item_id': 1 if i % 2 else 2, 'statut': 'active',
        }
    for params, expected in [
        ({}, list(range(1, 21))),
        ({'limit': 100}, list(range(1, 26))),
        ({'item_id': 2, 'limit': 2}, [2, 4]),
        ({'item_id': 999}, []),
    ]:
        response = client.get('/reservations', params=params)
        assert response.status_code == 200
        assert [r['id'] for r in response.json()] == expected
