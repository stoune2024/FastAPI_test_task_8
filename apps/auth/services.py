from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

import jwt
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.utils import get_authorization_scheme_param
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from apps.user.services import ConnectionDep
from settings.settings import SettingsDep
from apps.auth.schemas import TokenData


class OAuth2PasswordBearerWithCookie(OAuth2PasswordBearer):
    """Расширяет функционал класса OAuth2PasswordBearer с целью получения JWT-токена из Cookie"""

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
        token = request.cookies.get("access-token")
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


def verify_password(plain_password, hashed_password):
    """
    Функция проверки соответствия полученного пароля и хранимого хеша
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_user(username: str, connection: ConnectionDep):
    """
    Функция получения информации о пользователе из БД
    :param username: Логин пользователя
    :param connection: Объект типа Connection (соединение) для взаимодействия с БД
    :return: Пользователь, валидированный моделью User
    """
    try:
        user = connection.read_user_by_username(username)
        return user
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
            headers={"WWW-Authenticate": "Bearer"},
        )


def authenticate_user(username: str, password: str, connection: ConnectionDep):
    """
    Функция аутентификации пользователя
    :param username: Логин пользователя
    :param password: Пароль пользователя
    :param connection: Объект типа Connection (соединение) для взаимодействия с БД
    :return: Пользователь, валидированный моделью User
    """
    user = get_user(username, connection)
    if not verify_password(password, user["hashed_password"]):
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
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


async def verify_token(
    settings: SettingsDep,
    token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    connection: ConnectionDep,
):
    """
    Функция проверки JWT-токена пользователя и возврата токена с username пользователя, если все в порядке.
    :param settings: Объект-настройки для взаимодействия с переменными окружения из .env-файла
    :param token: JWT-токен пользователя, полученный из cookie-файла
    :param request: Объект-запрос
    :param connection: Объект типа Connection (соединение) для взаимодействия с БД
    :return: username-пользователя, декодированный из токена доступа
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
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
            detail="Токен доступа не действителен",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = get_user(token_data.username, connection)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не авторизован!",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data


ProtectionDep = Annotated[TokenData, Depends(verify_token)]
