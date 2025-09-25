from typing import Annotated, Any
from fastapi import Depends
from pydantic.dataclasses import dataclass
from settings.settings import settings
from apps.user.schemas import UserCreate, User


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__()
            cls._instances[cls] = instance
        return cls._instances[cls]


@dataclass
class UsersStore(metaclass=SingletonMeta):
    """
    Хранилище Пользователей
    """

    _users_store = []

    @property
    def users_store(self):
        # print(self._users_store)
        return self._users_store

    def __call__(self, user_dict):
        # print(self._users_store)
        self._users_store.append(user_dict)
        # print(self._users_store)


users_store_instance = UsersStore()


class DatabaseConnection:
    """
    Контекстный менеджер, имитирующий подключение к БД
    """

    def __init__(self, db_url):
        self.db_url = db_url

    def __enter__(self):
        try:
            print(f"Подключение к базе данных с URL: {settings.db_url}")
            return self
        except:
            print("Ошибка при подключении к БД")

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            print(f"Отключение от базы данных с URL: {settings.db_url}")
            print("Отключение от базы данных")
        except:
            print("Ошибка при разрыве подключения с БД")

    def create_user(self, user: User):
        user_dict = user.model_dump()
        users_store_instance(user_dict)

    def read_users(self):
        return users_store_instance.users_store


def get_connection():
    with DatabaseConnection(settings.db_url) as connection:
        yield connection


ConnectionDep = Annotated[Any, Depends(get_connection)]
