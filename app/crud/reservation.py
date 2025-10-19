from typing import List, Optional
from datetime import datetime as dt

from sqlalchemy import select, and_, between, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models import Reservation, User


class CRUDReservation(CRUDBase):

    # async def get_reservations_at_the_same_time(
    #     self,
    #     from_reserve: dt,
    #     to_reserve: dt,
    #     meetingroom_id: int,
    #     session: AsyncSession,
    # ) -> List[Reservation]:
    #     # #  Вариант 1:
    #     # #  Запрос на определения свободного окна времени для переговорки.
    #     # Выбрать такие объекты Reservation, где выполняются следующие условия:
    #     # номер переговорки равен заданному
    #     # и верно одно из следующих условий:
    #     #     или начало брони между началом и концом объекта,
    #     #     или конец брони между началом и концом объекта,
    #     #     или (начало брони меньше начала объекта
    #     #         и конец брони больше конца объекта).
    #     # Reservation = await session.execute(
    #     #     select(Reservation).where(
    #     #         Reservation.meetingroom_id == meetingroom_id,
    #     #         or_(
    #     #             between(
    #     #                 from_reserve,
    #     #                 Reservation.from_reserve,
    #     #                 Reservation.to_reserve
    #     #             ),
    #     #             between(
    #     #                 to_reserve,
    #     #                 Reservation.from_reserve,
    #     #                 Reservation.to_reserve
    #     #             ),
    #     #             and_(
    #     #                 from_reserve <= Reservation.from_reserve,
    #     #                 to_reserve >= Reservation.to_reserve
    #     #             )
    #     #         )
    #     #     )
    #     # )
    #     # Reservation = Reservation.scalars().all()
    #     # return Reservation
    #     # # #  Вариант 2:
    #     # # #  Запрос на определения свободного окна времени для переговорки.
    #     # # Выбрать такие объекты Reservation, где выполняются следующие условия:
    #     # # номер переговорки равен заданному
    #     # # и верны следующие условия:
    #     # #     начало бронирования меньше конца
    #     # #         существующего объекта бронирования,
    #     # #     окончание бронирования больше начала
    #     # #         существующего объекта бронирования.
    #     # reservations = await session.execute(
    #     #     select(Reservation).where(
    #     #         Reservation.meetingroom_id == meetingroom_id,
    #     #         and_(
    #     #             from_reserve <= Reservation.to_reserve,
    #     #             to_reserve >= Reservation.from_reserve
    #     #         )
    #     #     )
    #     # )
    #     # reservations = reservations.scalars().all()
    #     # return reservations

    async def get_reservations_at_the_same_time(
        self,
            # Добавляем звёздочку, чтобы обозначить, что все дальнейшие параметры
            # должны передаваться по ключу. Это позволит располагать
            # параметры со значением по умолчанию перед параметрами без таких значений.
            *,
            from_reserve: dt,
            to_reserve: dt,
            meetingroom_id: int,
            # Добавляем новый опциональный параметр - id объекта бронирования.
            reservation_id: Optional[int] = None,
            session: AsyncSession,
    ) -> list[Reservation]:
        # Выносим уже существующий запрос в отдельное выражение.
        select_stmt = select(Reservation).where(
            Reservation.meetingroom_id == meetingroom_id,
            and_(
                from_reserve <= Reservation.to_reserve,
                to_reserve >= Reservation.from_reserve
            )
        )
        # Если передан id бронирования...
        if reservation_id is not None:
            # ... то к выражению нужно добавить новое условие.
            select_stmt = select_stmt.where(
                # id искомых объектов не равны id обновляемого объекта.
                Reservation.id != reservation_id
            )
        # Выполняем запрос.
        reservations = await session.execute(select_stmt)
        reservations = reservations.scalars().all()
        return reservations

    async def get_future_reservations_for_room(
        self,
        room_id: int,
        session: AsyncSession
    ) -> list[Reservation]:
        rooms_reservations = await session.execute(
            select(Reservation).where(
                Reservation.meetingroom_id == room_id,
                Reservation.to_reserve > dt.now()
            )
        )
        rooms_reservations = rooms_reservations.scalars().all()
        return rooms_reservations

    async def get_by_user(
        self,
        user: User,
        session: AsyncSession
    ) -> list[Reservation]:
        reservation_user = await session.execute(
            select(Reservation).where(
                Reservation.user_id == user.id
            )
        )
        reservation_user = reservation_user.scalara().all()
        return reservation_user


reservation_crud = CRUDReservation(Reservation)
