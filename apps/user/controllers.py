from apps.user.routers import user_router
from apps.user.schemas import UserPublic, UserCreate, User
from apps.user.repository import ConnectionDep
from fastapi import Form, Query
from typing import Annotated
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@user_router.post("/users/")
def create_user(
    user: Annotated[UserCreate, Form()],
    connection: ConnectionDep,
):
    """
    Эндпоинт создания (регистрации нового пользователя)
    :param user: Данные о пользователе, приходящие из HTML формы. Валидируются Pydantic моделью UserCreate
    :param connection: Объект типа Connection (соединение) для взаимодействия с БД
    :return: JSON-объект, сообщающий о результате выполнения эндпоинта и возвращающий пользователя в виде словаря
    """
    try:
        user_dict = user.model_dump()
        hashed_password = pwd_context.hash(user.password)
        extra_data = {"hashed_password": hashed_password}
        user_dict.update(extra_data)
        user_model = User.model_validate(user_dict)
        connection.create_user(user_model)
        return {"message": f"user is created, his dict is: {user_dict}"}
    except (AttributeError, Exception) as e:
        return {"message": f"something_went_wrong...{e}"}


@user_router.get(
    "/users/",
    # response_model=list[UserPublic]
)
def read_users(
    connection: ConnectionDep,
    offset: Annotated[
        int,
        Query(
            title="Отступ для списка пользователей",
            ge=0,
            le=1000,
        ),
    ] = 0,
    limit: Annotated[
        int, Query(title="Ограначитель списка пользователей", ge=0, le=1000)
    ] = 10,
):
    """
    Эндпоинт получения списка пользователей.
    :param connection: Объект типа Connection (соединение) для взаимодействия с БД
    :param offset: Отступ для списка пользователей (условно их максимум 1000). Используется для пагинации
    :param limit: Ограничитель максимального количества отображаемых пользователей. Используется для пагинации.
    :return: Список пользователей, валидированных моделью UserPublic
    """
    list_of_users = connection.read_users()
    return list_of_users
