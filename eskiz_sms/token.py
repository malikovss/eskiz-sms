from dotenv import get_key, set_key

from .logging import logger
from .request import BaseRequest

ESKIZ_TOKEN_KEY = "ESKIZ_TOKEN"


class Token(BaseRequest):
    __slots__ = (
        "auto_update",
        "save_token",
        "env_file_path",
        "_value",
        "_credentials",
        "updated_at",
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

        self.__token_checked = False

    def set(self, value):
        self._value = value

    def _save_to_env(self):
        set_key(self.env_file_path, key_to_set=ESKIZ_TOKEN_KEY,
                value_to_set=self._value)
        logger.info(f"Eskiz token saved to {self.env_file_path}")

    def _get_from_env(self):
        return get_key(dotenv_path=self.env_file_path, key_to_get=ESKIZ_TOKEN_KEY)

    def __str__(self):
        if self._value:
            return self._value
        return "None"

    __repr__ = __str__

    def _get(self, get_new: bool = False):
        if get_new:
            return self._get_new_token()

        if self._value and self.__token_checked:
            return self._value

        if not self._value:
            if self.save_token:
                self._value = self._get_from_env()
            if not self._value:
                self._value = self._get_new_token()
                if self.save_token:
                    self._save_to_env()
        if not self.__token_checked:
            self._check()

        return self._value

    def get(self, get_new: bool = False):
        if self._is_async:
            return self._aget(get_new)
        return self._get(get_new)

    def _get_new_token(self) -> str:
        response = self._request(
            self._prepare_request(
                "POST",
                "/auth/login",
                self._credentials
            )
        )
        self.__token_checked = True
        return response.data['data']['token']

    def _check(self):
        self._request(
            self._prepare_request(
                "GET",
                "/auth/user",
                headers={
                    'Authorization': f'Bearer {self._value}'
                }
            )
        )
        self.__token_checked = True

    # =====Async functions==== #
    async def _aget(self, get_new: bool = False):
        if get_new:
            return await self._aget_new_token()

        if self._value and self.__token_checked:
            return self._value

        if not self._value:
            if self.save_token:
                self._value = self._get_from_env()
            if not self._value:
                self._value = await self._aget_new_token()
                if self.save_token:
                    self._save_to_env()
        if not self.__token_checked:
            await self._acheck()

        return self._value

    async def _acheck(self):
        await self._a_request(
            self._prepare_request(
                "GET",
                "/auth/user",
                headers={
                    'Authorization': f'Bearer {self._value}'
                }
            )
        )
        self.__token_checked = True

    async def _aget_new_token(self):
        response = await self._a_request(
            self._prepare_request(
                "POST",
                "/auth/login",
                self._credentials
            )
        )
        self.__token_checked = True
        return response.data['data']['token']
