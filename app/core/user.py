"""Вспомогательные компоненты аутентификации пользователей на базе FastAPI Users.

Модуль объединяет транспорт для выдачи токенов, JWT-стратегию
и менеджер пользователей с дополнительной валидацией паролей.
"""

from typing import Optional, Union

from fastapi import Depends, Request
from fastapi_users import (
    BaseUserManager, FastAPIUsers, IntegerIDMixin, InvalidPasswordException
)
from fastapi_users.authentication import (
    AuthenticationBackend, BearerTransport, JWTStrategy
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_async_session
from app.models import User
from app.schemas.user import UserCreate


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    """Предоставляет доступ к уровню хранения пользователей.

    Аргументы:
        session (AsyncSession): Асинхронная сессия SQLAlchemy,
            полученная из контейнера зависимостей приложения.

    Возвращает:
        SQLAlchemyUserDatabase: Класс хранилища, выполняющий операции
            с таблицей пользователей.
    """
    yield SQLAlchemyUserDatabase(session, User)


# Транспорт определяет endpoint, который отвечает за выдачу JWT-токенов.
bearer_transport = BearerTransport(tokenUrl='auth/jwt/login')


def get_jwt_strategy() -> JWTStrategy:
    """Создаёт JWT-стратегию с настройками приложения.

    Возвращает:
        JWTStrategy: Стратегия с секретом проекта и временем жизни токена,
            заданным в секундах.
    """
    return JWTStrategy(secret=settings.secret, lifetime_seconds=3600)


# Backend аутентификации объединяет транспорт и стратегию.
auth_backend = AuthenticationBackend(
    name='jwt',
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    """Управляет жизненным циклом пользователей и хуками аутентификации.

    Наследует базовый менеджер FastAPI Users, добавляя
    пользовательскую проверку пароля и действия, выполняемые после регистрации.

    Аргументы:
        user_db (SQLAlchemyUserDatabase): Объект доступа к данным пользователя,
            предоставляемый инфраструктурой FastAPI Users.
    """

    async def validate_password(
        self,
        password: str,
        user: Union[UserCreate, User],
    ) -> None:
        """Проверяет пароль пользователя на соответствие базовым требованиям.

        Аргументы:
            password (str): Пароль, введённый пользователем.
            user (Union[UserCreate, User]): Объект пользователя (нового или
                существующего), для которого выполняется проверка.

        Возвращает:
            None: Корутинa завершается без результата, если пароль корректен.

        Исключения:
            InvalidPasswordException: Выбрасывается, если пароль слишком
                короткий или содержит адрес электронной почты пользователя.
        """
        if len(password) < 3:
            raise InvalidPasswordException(
                reason='Password should be at least 3 characters'
            )
        if user.email in password:
            raise InvalidPasswordException(
                reason='Password should not contain e-mail'
            )

    async def on_after_register(
        self,
        user: User,
        request: Optional[Request] = None
    ):
        """Выполняет побочные действия после завершения регистрации.

        Аргументы:
            user (User): Экземпляр только что зарегистрированного пользователя.
            request (Optional[Request]): Исходный HTTP-запрос, если доступен.

        Возвращает:
            None: Используется для побочных действий, например логирования.
        """
        print(f'Пользователь {user.email} зарегистрирован.')


async def get_user_manager(user_db=Depends(get_user_db)):
    """Предоставляет менеджер пользователей через зависимости FastAPI.

    Аргументы:
        user_db: Зависимость, возвращающая доступ к обёртке базы данных пользователей.

    Возвращает:
        UserManager: Настроенный менеджер, работающий с хранилищем пользователей.
    """
    yield UserManager(user_db)


# FastAPI Users связывает менеджер с backend-ом аутентификации.
fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend]
)


# Зависимости, возвращающие текущего пользователя или суперпользователя.
current_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)
