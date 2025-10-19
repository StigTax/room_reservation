from typing import Optional

from datetime import datetime as dt, timedelta as td

from pydantic import (
    BaseModel, validator, root_validator, Extra, Field
)

FROM_TIME = (
    dt.now() + td(minutes=10)
).isoformat(timespec="minutes")
TO_TIME = (
    dt.now() + td(minutes=60)
).isoformat(timespec="minutes")


class ReservationBase(BaseModel):
    from_reserve: dt = Field(..., example=FROM_TIME)
    to_reserve: dt = Field(..., example=TO_TIME)

    class Config:
        extra = Extra.forbid


class ReservationUpdate(ReservationBase):
    pass

    @validator('from_reserve')
    def check_from_reserve_later_than_now(cls, value: dt):
        if value <= dt.now():
            raise ValueError('Start time must be in the future!')
        return value

    @root_validator
    def check_from_reserve_before_to_reserve(cls, values):
        from_reserve = values.get('from_reserve')
        to_reserve = values.get('to_reserve')
        if from_reserve is None or to_reserve is None:
            return values
        if from_reserve >= to_reserve:
            raise ValueError('Reservation start must be before the finish!')
        return values


class ReservationCreate(ReservationUpdate):
    meetingroom_id: int


class ReservationDB(ReservationBase):
    id: int
    meetingroom_id: int
    user_id: Optional[int]

    class Config:
        orm_mode = True
