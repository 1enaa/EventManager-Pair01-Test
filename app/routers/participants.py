from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Participant
from ..schemas import (
    Participant as ParticipantSchema,
    ParticipantCreate
)


router = APIRouter(
    prefix="/participants",
    tags=["Participants"]
)


@router.post(
    "/",
    response_model=ParticipantSchema,
    status_code=status.HTTP_201_CREATED
)
def create_participant(
    participant: ParticipantCreate,
    db: Session = Depends(get_db)
):
    existing = (
        db.query(Participant)
        .filter(Participant.email == participant.email)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Email is already registered."
        )

    db_participant = Participant(
        **participant.model_dump()
    )

    db.add(db_participant)
    db.commit()
    db.refresh(db_participant)

    return db_participant


@router.get(
    "/",
    response_model=list[ParticipantSchema]
)
def list_participants(
    db: Session = Depends(get_db)
):
    return (
        db.query(Participant)
        .order_by(Participant.name)
        .all()
    )


@router.get(
    "/{participant_id}",
    response_model=ParticipantSchema
)
def get_participant(
    participant_id: int,
    db: Session = Depends(get_db)
):
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

    return participant


@router.delete(
    "/{participant_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_participant(
    participant_id: int,
    db: Session = Depends(get_db)
):
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

    db.delete(participant)
    db.commit()