from datetime import timedelta
from typing import Annotated

from fastapi import HTTPException, status, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm

from apps.auth.routers import auth_router
from apps.user.services import ConnectionDep
from settings.settings import SettingsDep
from apps.auth.services import authenticate_user, create_access_token


@auth_router.post("/login")
async def validate_login_form(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    connection: ConnectionDep,
    settings: SettingsDep,
):
    """
    Эндпоинт отвечает за обработку данных, пришедших из формы авторизации. Если пользователь успешно прошел
    аутентификацию и авторизацию JWT-токен сохраняется в куках. Происходит перенаправление на другую страницу.
    :param request: Объект-запрос
    :param form_data: HTML форма с полями username и password. Используется Oauth2
    :param connection: Объект типа Connection (соединение) для взаимодействия с БД
    :param settings: Объект-настройки для взаимодействия с переменными окружения из .env-файла
    :return: Перенаправление на другую страницу
    """
    token = await login_for_access_token(request, form_data, connection, settings)
    access_token = token.get("access_token")
    redirect_url = "/auth/suc_auth"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = RedirectResponse(
        redirect_url, status_code=status.HTTP_303_SEE_OTHER, headers=headers
    )
    response.set_cookie(
        key="access-token", value=access_token, httponly=True, secure=True
    )
    return response


@auth_router.post("/token")
async def login_for_access_token(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    connection: ConnectionDep,
    settings: SettingsDep,
):
    """
    Эндпоинт отвечает за аутентификацию пользователя и генерацию JWT-токена. Функция работает как зависимость
    в эндпоинте POST /login
    :param request: Объект-запрос
    :param form_data: HTML форма с полями username и password. Используется Oauth2
    :param connection: Объект типа Connection (соединение) для взаимодействия с БД
    :param settings: Объект-настройки для взаимодействия с переменными окружения из .env-файла
    :return: JSON-объект с данными о токене доступа
    """
    user = authenticate_user(form_data.username, form_data.password, connection)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        settings, data={"sub": user['username']}, expires_delta=access_token_expires
    )

    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_access_token(
        settings, data={"sub": user['username'], "type": "refresh"}, expires_delta=refresh_token_expires
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@auth_router.get("/suc_auth")
def successfull_auth():
    """
    Эндпоинт для редиректа после успешной авторизации
    :return: JSON-оповещение
    """
    return {"message": "Авторизация успешна, токен доступа сохранен в куках!"}
