from typing import Annotated, Any
from fastapi import Depends
from settings.settings import settings
from apps.user.schemas import User
from apps.user.repository import users_store_instance


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
        except Exception as e:
            print(f"Ошибка при подключении к БД: {e}")

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            print(f"Отключение от базы данных с URL: {settings.db_url}")
            print("Отключение от базы данных")
        except Exception as e:
            print(f"Ошибка при разрыве подключения с БД: {e}")

    def create_user(self, user: User):
        user_dict = user.model_dump()
        users_store_instance(user_dict)

    def read_user_by_id(self, user_id):
        users_list = users_store_instance.users_store
        for i in users_list:
            if i["id"] == user_id:
                return i

    def read_users(self, start, end):
        users_list = users_store_instance.users_store
        if start is None and end is None:
            return users_list
        return users_list[start - 1 : end]

    def delete_user(self, user_id):
        users_list = users_store_instance.users_store
        for i in users_list:
            if i["id"] == user_id:
                users_list.remove(i)


def get_connection():
    with DatabaseConnection(settings.db_url) as connection:
        yield connection


ConnectionDep = Annotated[Any, Depends(get_connection)]
