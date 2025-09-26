from apps.user.routers import user_router
from apps.user.schemas import UserPublic, UserCreate, User
from apps.user.services import ConnectionDep
from fastapi import Form, Query, Path, HTTPException, Body
from fastapi.exceptions import ResponseValidationError
from typing import Annotated
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@user_router.post("/user/")
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


@user_router.post("/users/")
def create_users(
    users: Annotated[list[UserCreate], Body()],
    connection: ConnectionDep,
):
    """
    Эндпоинт создания группы пользователей
    :param users: Список пользователей, пришедших из тела запроса
    :param connection: Объект типа Connection (соединение) для взаимодействия с БД
    :return: JSON-объект, сообщающий о результате выполнения эндпоинта и возвращающий список пользователей
    """
    try:
        list_of_users = []
        for user in users:
            user_dict = user.model_dump()
            hashed_password = pwd_context.hash(user.password)
            extra_data = {"hashed_password": hashed_password}
            user_dict.update(extra_data)
            list_of_users.append(user_dict)
            user_model = User.model_validate(user_dict)
            connection.create_user(user_model)
        return {"message": f"Пользователи созданы!: {list_of_users}"}

    except Exception as e:
        return {"message": f"Произошла ошибка: {e}"}


@user_router.get("/users/{user_id}", response_model=UserPublic)
def read_user(
    connection: ConnectionDep,
    user_id: Annotated[int, Path(title="Идентификатор пользователя", ge=0, le=1000)],
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


@user_router.get("/users/", response_model=list[UserPublic])
def read_users_list(
    connection: ConnectionDep,
    start_index: Annotated[
        int,
        Query(
            title="Начало поиска",
            description="ID пользователя, с которого начать поиск",
            ge=0,
            le=1000,
        ),
    ] = None,
    end_index: Annotated[
        int,
        Query(
            title="Конец поиска",
            description="ID пользователя, которым закончить поиск",
            ge=0,
            le=1000,
        ),
    ] = None,
):
    """
    Эндпоинт получения списка пользователей по списку ID.
    :param connection: Объект типа Connection (соединение) для взаимодействия с БД
    :param start_index: Значение ID, с которого начинается поиск пользователей
    :param end_index: Значение ID, которым заканчивается поиск пользователей.
    :return: Список пользователей, валидированных моделью UserPublic
    """
    try:
        users_list = connection.read_users(start_index, end_index)
        return users_list
    except Exception as e:
        return {"message": f"Возникла ошибка: {e}"}


@user_router.patch("/users/{user_id}", response_model=UserPublic)
def update_user(
    user_id: Annotated[int, Path(title="Идентификатор пользователя", ge=0, le=1000)],
    user: Annotated[UserCreate, Form()],
    connection: ConnectionDep,
):
    """
    Эндпоинт обновления данных о пользователе.
    :param user_id: Параметр пути, обозначающий идентификатор искомого пользователя.
    :param user: Данные о пользователе, приходящие из HTML формы. Валидируются Pydantic моделью UserUpdate
    :param connection: Объект типа Connection (соединение) для взаимодействия с БД
    :return: Объект пользователь, валидируемый моделью UserPublic
    """
    try:
        user_from_db = connection.read_user_by_id(user_id)
        if not user_from_db:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        user_data = user.model_dump(exclude_unset=True)
        extra_data = {}
        if "password" in user_data:
            password = user_data["password"]
            hashed_password = pwd_context.hash(password)
            extra_data["hashed_password"] = hashed_password
        del user_data["password"]
        user_from_db.update(user_data)
        user_from_db.update(extra_data)
        return user_from_db
    except Exception as e:
        return {"message": f"Возникла ошибка: {e}"}


@user_router.delete("/users/{user_id}")
def delete_user(
    user_id: Annotated[int, Path(title="Идентификатор пользователя", ge=0, le=1000)],
    connection: ConnectionDep,
):
    """
    Эндпоинт удаления данных о конкретном пользователе
    :param user_id: Параметр пути, обозначающий идентификатор искомого пользователя.
    :param connection: Объект типа Connection (соединение) для взаимодействия с БД
    :return: JSON-объект, сообщающий о результате выполнения эндпоинта (возврат пользователя)
    """
    try:
        connection.delete_user(user_id)
        return {"message": f"User with ID: {user_id} has been deleted succesfully"}
    except Exception as e:
        return {"message": f"Возникла ошибка: {e}"}
