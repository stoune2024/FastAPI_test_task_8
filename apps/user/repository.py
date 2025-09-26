from pydantic.dataclasses import dataclass


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
        return self._users_store

    def __call__(self, user_dict):
        self._users_store.append(user_dict)


users_store_instance = UsersStore()
