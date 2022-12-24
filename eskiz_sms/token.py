from datetime import datetime
from typing import Optional

from dotenv import get_key, set_key

from .request import BaseRequest
from .logging import logger

ESKIZ_TOKEN_KEY = "ESKIZ_TOKEN"


class Token(BaseRequest):
    __slots__ = (
        "auto_update",
        "save_token",
        "env_file_path",
        "_value",
        "_credentials",
        "__last_updated_at",
        "__token_checked",
    )

    def __init__(
            self,
            email: str,
            password: str,
            save_token=False,
            env_file_path=None,
            auto_update: bool = True,
            is_async: bool = False,
    ):
        self._is_async = is_async
        self.auto_update = auto_update
        self.save_token = save_token

        self._value = None
        self._credentials = dict(email=email, password=password)

        if save_token:
            if env_file_path is None:
                env_file_path = '.env'
            self.env_file_path = env_file_path

        self.__last_updated_at: Optional[datetime] = None
        self.__token_checked = False

    def set(self, value):
        self._value = value

    def _save_token_to_env(self, _token):
        set_key(self.env_file_path, key_to_set=ESKIZ_TOKEN_KEY,
                value_to_set=_token)
        logger.info(f"Eskiz token saved to {self.env_file_path}")
        return _token

    def _get_token_from_env(self):
        return get_key(dotenv_path=self.env_file_path, key_to_get=ESKIZ_TOKEN_KEY)

    def update(self):
        raise NotImplementedError

    def __str__(self):
        return self._value

    __repr__ = __str__

    def _get_token_sync(self):
        pass

    async def _get_token_async(self):
        pass

    def get(self):
        if self._is_async:
            return self._get_token_async()
        return self._get_token_sync()
