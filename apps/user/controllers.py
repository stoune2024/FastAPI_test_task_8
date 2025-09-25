from apps.user.routers import user_router
from apps.user.schemas import UserPublic, UserCreate, User
from apps.user.repository import ConnectionDep
from fastapi import Form, Query, Path, HTTPException
from fastapi.exceptions import ResponseValidationError
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


@user_router.get("/users/",response_model=list[UserPublic])
def read_users(
    connection: ConnectionDep,
):
    """
    Эндпоинт получения списка всех пользователей.
    :param connection: Объект типа Connection (соединение) для взаимодействия с БД
    :return: Список пользователей, валидированных моделью UserPublic
    """
    try:
        list_of_users = connection.read_users()
        return list_of_users
    except Exception as e:
        return {"message": f"something_went_wrong...{e}"}


@user_router.get("/users/{user_id}", response_model=UserPublic)
def update_user(
        connection: ConnectionDep,
        user_id: Annotated[
            int,
            Path(
                title='Идентификатор пользователя',
                ge=0,
                le=1000
            )
        ],
):
    """
    Эндпоинт получения конкретного пользователя по идентификатору из БД.
    :param connection: Объект типа Connection (соединение) для взаимодействия с БД
    :param user_id: Параметр пути, обозначающий идентификатор искомого пользователя.
    :return: Объект пользователь, валидируемый моделью UserPublic
    """
    try:
        user_dict = connection.read_user_by_id(user_id)
        if not user_dict:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        return user_dict
    except ResponseValidationError:
        return {"message": "Фастапи ругается на какую-то &$*^ю"}
    except Exception as e:
        return {"message": f"something_went_wrong...{e}"}


