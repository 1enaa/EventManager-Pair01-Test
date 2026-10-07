from sqlalchemy import Column, Date, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from .database import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    date = Column(Date, nullable=False)
    location = Column(String(100), nullable=False)
    capacity = Column(Integer, nullable=False)

    registrations = relationship(
        "Registration",
        back_populates="event",
        cascade="all, delete-orphan"
    )


class Participant(Base):
    __tablename__ = "participants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), nullable=False, unique=True, index=True)

    registrations = relationship(
        "Registration",
        back_populates="participant",
        cascade="all, delete-orphan"
    )


class Registration(Base):
    __tablename__ = "registrations"

    id = Column(Integer, primary_key=True, index=True)

    event_id = Column(
        Integer,
        ForeignKey("events.id"),
        nullable=False
    )

    participant_id = Column(
        Integer,
        ForeignKey("participants.id"),
        nullable=False
    )

    event = relationship(
        "Event",
        back_populates="registrations"
    )

    participant = relationship(
        "Participant",
        back_populates="registrations"
    )

    __table_args__ = (
        UniqueConstraint(
            "event_id",
            "participant_id",
            name="uq_event_participant"
        ),
    )