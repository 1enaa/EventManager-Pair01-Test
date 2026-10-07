from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class EventBase(BaseModel):
    title: str = Field(min_length=3, max_length=100)
    description: str | None = None
    date: date
    location: str = Field(min_length=2, max_length=100)
    capacity: int = Field(gt=0, le=10000)


class EventCreate(EventBase):
    pass


class EventUpdate(EventBase):
    pass


class Event(EventBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class ParticipantBase(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr


class ParticipantCreate(ParticipantBase):
    pass


class Participant(ParticipantBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class Registration(BaseModel):
    id: int
    event_id: int
    participant_id: int

    model_config = ConfigDict(from_attributes=True)