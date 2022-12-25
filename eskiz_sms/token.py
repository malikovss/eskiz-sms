from datetime import datetime
from typing import Optional

from dotenv import get_key, set_key

from .exceptions import EskizException
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

        self.updated_at: Optional[datetime] = None
        self.__token_checked = False

    def set(self, value):
        self._value = value

    def _save_to_env(self):
        set_key(self.env_file_path, key_to_set=ESKIZ_TOKEN_KEY,
                value_to_set=self._value)
        logger.info(f"Eskiz token saved to {self.env_file_path}")

    def _get_from_env(self):
        return get_key(dotenv_path=self.env_file_path, key_to_get=ESKIZ_TOKEN_KEY)

    def update(self):
        if self.updated_at and (self.updated_at - datetime.now()).days < 29:
            raise EskizException(message="Can't update too fast")
        request = self._prepare_request(
            "PATCH",
            "/auth/refresh",
            headers={
                "Authorization": f"Bearer {self._value}"
            }
        )
        if self._is_async:
            return self._a_update(request)
        return self._update(request)

    def __str__(self):
        if self._value:
            return self._value
        return "None"

    __repr__ = __str__

    def _get(self):
        if self.save_token:
            self._value = self._get_from_env()
        if not self._value:
            self._value = self._get_new_token()
            self._check()
            if self.save_token:
                self._save_to_env()
        return self._value

    def _update(self, request):
        self._request(request)
        self.updated_at = datetime.now()

    def get(self):
        if self._value and self.__token_checked:
            return self._value

        if self._is_async:
            return self._a_get()
        return self._get()

    def _get_new_token(self):
        response = self._request(
            self._prepare_request(
                "POST",
                "/auth/login",
                self._credentials
            )
        )
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
    async def _a_get(self):
        if self.save_token:
            self._value = self._get_from_env()
            await self._a_check()
        if not self._value:
            self._value = await self._a_get_new_token()
            if self.save_token:
                self._save_to_env()
        return self._value

    async def _a_update(self, request):
        await self._a_request(request)
        self.updated_at = datetime.now()

    async def _a_check(self):
        await self._a_request(
            self._prepare_request(
                "PATCH",
                "/auth/user",
                headers={
                    'Authorization': f'Bearer {self._value}'
                }
            )
        )
        self.__token_checked = True

    async def _a_get_new_token(self):
        response = await self._a_request(
            self._prepare_request(
                "POST",
                "/auth/login",
                self._credentials
            )
        )
        return response.data['data']['token']
