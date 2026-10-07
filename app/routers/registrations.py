from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Event, Participant, Registration
from ..schemas import Registration as RegistrationSchema


router = APIRouter(
    prefix="/events",
    tags=["Registrations"]
)


@router.post(
    "/{event_id}/register/{participant_id}",
    response_model=RegistrationSchema,
    status_code=status.HTTP_201_CREATED
)
def register_participant(
    event_id: int,
    participant_id: int,
    db: Session = Depends(get_db)
):
    # Check that the event exists
    event = (
        db.query(Event)
        .filter(Event.id == event_id)
        .first()
    )

    if not event:
        raise HTTPException(
            status_code=404,
            detail="Event not found."
        )

    # Check that the participant exists
    participant = (
        db.query(Participant)
        .filter(Participant.id == participant_id)
        .first()
    )

    if not participant:
        raise HTTPException(
            status_code=404,
            detail="Participant not found."
        )

    # Check for duplicate registration
    existing = (
        db.query(Registration)
        .filter(
            Registration.event_id == event_id,
            Registration.participant_id == participant_id
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Participant is already registered."
        )

    # Check event capacity
    if len(event.registrations) >= event.capacity:
        raise HTTPException(
            status_code=409,
            detail="Event capacity has been reached."
        )

    registration = Registration(
        event_id=event_id,
        participant_id=participant_id
    )

    db.add(registration)
    db.commit()
    db.refresh(registration)

    return registration


@router.get(
    "/{event_id}/participants"
)
def list_event_participants(
    event_id: int,
    db: Session = Depends(get_db)
):
    event = (
        db.query(Event)
        .filter(Event.id == event_id)
        .first()
    )

    if not event:
        raise HTTPException(
            status_code=404,
            detail="Event not found."
        )

    return [
        {
            "id": registration.participant.id,
            "name": registration.participant.name,
            "email": registration.participant.email
        }
        for registration in event.registrations
    ]