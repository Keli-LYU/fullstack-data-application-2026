from fastapi import APIRouter, HTTPException, Path, Query

from app.schemas.reservation import ReservationCreate, ReservationRead

router = APIRouter(prefix="/reservations", tags=["reservations"])

FAKE_DB: dict[int, dict] = {}
def _next_id() -> int:
    return max(FAKE_DB, default=0) + 1


@router.post("", response_model=ReservationRead, status_code=201)
def create_reservation(payload: ReservationCreate):
    reservation_id = _next_id()
    reservation = {"id": reservation_id, **payload.model_dump(), "statut": "active"}
    FAKE_DB[reservation_id] = reservation
    return reservation


@router.get("", response_model=list[ReservationRead])
def list_reservations(
    item_id: int | None = Query(default=None, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    reservations = list(FAKE_DB.values())
    if item_id is not None:
        reservations = [
            reservation for reservation in reservations if reservation["item_id"] == item_id
        ]
    return reservations[:limit]


@router.get("/{reservation_id}", response_model=ReservationRead)
def get_reservation(reservation_id: int = Path(ge=1)):
    reservation = FAKE_DB.get(reservation_id)
    if reservation is None:
        raise HTTPException(
            status_code=404, detail=f"Reservation {reservation_id} introuvable"
        )
    return reservation


@router.post("/{reservation_id}/annuler", response_model=ReservationRead)
def cancel_reservation(reservation_id: int = Path(ge=1)):
    reservation = get_reservation(reservation_id)
    if reservation["statut"] == "annulee":
        raise HTTPException(
            status_code=409, detail=f"Reservation {reservation_id} deja annulee"
        )
    reservation["statut"] = "annulee"
    return reservation
