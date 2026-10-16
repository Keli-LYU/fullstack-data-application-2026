from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.item import ItemUpdate
from app.schemas.reservation import ReservationCreate


@pytest.mark.parametrize('date_fin', [date(2026, 9, 1), date(2026, 8, 31)])
def test_schema_refuse_dates_egales_ou_inversees(date_fin):
    with pytest.raises(ValidationError, match='date_fin'):
        ReservationCreate(item_id=1, date_debut=date(2026, 9, 1), date_fin=date_fin)


def test_schema_accepte_reservation_valide():
    reservation = ReservationCreate(
        item_id=1, date_debut='2026-09-01', date_fin='2026-09-02',
    )
    assert reservation.date_debut == date(2026, 9, 1)
    assert reservation.date_fin == date(2026, 9, 2)


def test_item_update_vide_ne_fournit_aucun_champ():
    assert ItemUpdate().model_dump(exclude_unset=True) == {}


def test_item_update_distingue_description_nulle_et_absente():
    assert ItemUpdate(description=None).model_dump(exclude_unset=True) == {'description': None}
    assert ItemUpdate(titre='Tente').model_dump(exclude_unset=True) == {'titre': 'Tente'}
