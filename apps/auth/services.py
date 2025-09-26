from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional
from functools import lru_cache

import jwt
from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.security.utils import get_authorization_scheme_param
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.exc import InvalidRequestError
from sqlmodel import create_engine, Session, select, SQLModel

from settings.settings import settings
from apps.auth.routers import auth_router
from apps.auth.controllers import ConnectionDep, SettingsDep


class OAuth2PasswordBearerWithCookie(OAuth2PasswordBearer):
    """ Расширяет функционал класса OAuth2PasswordBearer с целью получения JWT-токена из Cookie"""

    async def __call__(self, request: Request) -> Optional[str]:
        authorization = request.headers.get("Authorization")
        if authorization is not None:
            scheme, param = get_authorization_scheme_param(authorization)
            if not authorization or scheme.lower() != "bearer":
                if self.auto_error:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Could not find Authorization header",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                else:
                    return None
            return param
        token = request.cookies.get('access-token')
        if token:
            param = token
            return param
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not find token",
                headers={"WWW-Authenticate": "Bearer"},
            )


# Контекст PassLib. Используется для хэширования и проверки паролей.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="token")



def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    """
Функция проверки соответствия полученного пароля и хранимого хеша
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_user(
        username: str,
        connection: ConnectionDep
):
    """
    Функция получения информации о пользователе из БД
    :param username: Логин пользователя
    :param connection: Объект типа Connection (соединение) для взаимодействия с БД
    :return: Пользователь, валидированный моделью User
    """
    try:
        user = connection.read_user_by_username(username)
        return user
    except InvalidRequestError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
            headers={"WWW-Authenticate": "Bearer"},
        )


def authenticate_user(
        username: str,
        password: str,
        connection: ConnectionDep
):
    """
    Функция аутентификации пользователя
    :param username: Логин пользователя
    :param password: Пароль пользователя
    :param connection: Объект типа Connection (соединение) для взаимодействия с БД
    :return: Пользователь, валидированный моделью User
    """
    user = get_user(username, connection)
    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Введен неверный пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def create_access_token(
        settings: SettingsDep,
        data: dict,
        expires_delta: timedelta | None = None,
):
    """
    Функция создания JWT-токена
    :param settings: Объект-настройки для взаимодействия с переменными окружения из .env-файла
    :param data: Словарь с ключом sub и значением логина пользователя
    :param expires_delta: Время истечения срока годности токена
    :return: JWT-токен, представляющий три строки, разделенные точками
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


async def verify_token(
        settings: SettingsDep,
        token: Annotated[str, Depends(oauth2_scheme)],
        request: Request,
        session: SessionDep
):
    """ Функция проверки JWT-токена пользователя и возврата токена с username пользователя, если все в порядке. """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not find token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = get_user(token_data.username, session)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not find user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data


router = APIRouter(tags=['Безопасность'])
