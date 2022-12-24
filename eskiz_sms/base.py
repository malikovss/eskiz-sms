from datetime import datetime
from json import JSONDecodeError
from typing import Optional

import httpx
from dotenv import get_key, set_key

from .exceptions import (
    EskizException,
    BadRequest,
    TokenBlackListed,
    TokenInvalid,
    InvalidCredentials,
    DecodeError,
    HTTPError
)
from .logging import logger
from .types import Response

ESKIZ_TOKEN_KEY = "ESKIZ_TOKEN"
BASE_URL = "https://notify.eskiz.uz/api"


class Base:
    @staticmethod
    def _url(path: str):
        return BASE_URL + path

    @staticmethod
    def _check_response(response: httpx.Response) -> httpx.Response:
        try:
            response.json()
        except JSONDecodeError:
            raise DecodeError("Internal server error")
        except httpx.HTTPError as e:
            raise HTTPError from e
        else:
            return response

    def _request(self, method: str, path: str, data: dict = None, headers: dict = None):
        with httpx.Client() as client:
            response = client.request(
                method=method,
                url=self._url(path),
                data=data,
                headers=headers
            )
            return self._check_response(response)

    async def _async_request(self, method: str, path: str, data: dict = None, headers: dict = None):
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=self._url(path),
                data=data,
                headers=headers
            )
            return self._check_response(response)


class Token(Base):
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
            auto_update: bool = True
    ):
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

    @property
    def value(self):
        if self._value is None:
            if self.save_token:
                _token = self._get_token_from_env()
                if not _token:
                    _token = self._get_new_token()
                    self._save_token_to_env(_token)
                else:
                    try:
                        self._check_token(_token)
                    except TokenInvalid:
                        logger.warning(
                            "Token is invalid. Getting new token"
                        )
                        _token = self._get_new_token()
                        self._save_token_to_env(_token)
                self._value = _token
            else:
                self._value = self._get_new_token()
        else:
            if not self.__token_checked:
                self._check_token(self._value)
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        self.__token_checked = False

    def set(self, value):
        self.value = value

    @property
    def headers(self):
        return {
            'Authorization': f'Bearer {self.value}'
        }

    def update(self):
        if self.__last_updated_at and (self.__last_updated_at - datetime.now()).days < 29:
            # It's for being sure that token isn't updating too fast. To avoid recursion.
            raise EskizException(message="Can't update too fast")
        else:
            self._check_token(self.value)
            self.__last_updated_at = datetime.now()

    def _check_token(self, _token: str):
        status_code, response = self._request(
            "PATCH",
            "/auth/refresh",
            headers={
                'Authorization': f'Bearer {_token}'
            }
        )
        if status_code == 401:
            response = Response(**response)
            raise TokenInvalid(status=response.status,
                               message=response.message)
        self.__token_checked = True

    def _save_token_to_env(self, _token):
        set_key(self.env_file_path, key_to_set=ESKIZ_TOKEN_KEY,
                value_to_set=_token)
        logger.info(f"Eskiz token saved to {self.env_file_path}")
        return _token

    def _get_token_from_env(self):
        return get_key(dotenv_path=self.env_file_path, key_to_get=ESKIZ_TOKEN_KEY)

    def _get_new_token(self):
        status_code, response = self._request(
            "POST",
            "/auth/login",
            data=self._credentials
        )
        response = Response(**response)
        if status_code == 401:
            raise InvalidCredentials(response.message)
        elif status_code != 200:
            raise BadRequest(response.message)
        return response.data.get('token')

    def __str__(self):
        return self.value

    __repr__ = __str__


class HelperMixin:
    @staticmethod
    def _prepare_payload(payload: dict):
        payload = payload or {}
        if 'from_whom' in payload:
            payload['from'] = payload.pop('from_whom')
        if 'mobile_phone' in payload:
            payload['mobile_phone'] = payload['mobile_phone'].replace(
                "+", "").replace(" ", "")
        return payload

    @staticmethod
    def _check_response(response: httpx.Response):
        logger.debug(
            f"Eskiz request status_code={response.status_code} body={response.json()}"
        )


class Request(Base, HelperMixin):

    def request(self, method: str, path: str, token: Token, payload: dict = None) -> dict:

        status_code, response = self._request(
            method,
            path,
            data=self._prepare_payload(payload),
            headers=token.headers
        )

        if status_code in [400, 401]:
            raise BadRequest(
                status=response['status'], message=response['message']
            )
        elif status_code == 500:
            if token.auto_update:
                token.update()
                return self.request(method, path, token, payload)
            raise TokenBlackListed(
                status=response['status'], message=response['message']
            )
        return response

    def post(self, path: str, token: Token, payload: dict = None):
        return self.request("POST", path, token, payload)

    def put(self, path: str, token: Token, payload: dict = None):
        return self.request("PUT", path, token, payload)

    def get(self, path: str, token: Token, params: Optional[dict] = None):
        return self.request("GET", path, token, params)

    def delete(self, path: str, token: Token, payload: dict = None):
        return self.request("DELETE", path, token, payload)

    def patch(self, path: str, token: Token, payload: dict = None):
        return self.request("PATCH", path, token, payload)


class AsyncRequest(Base):
    async def request(self, method: str, path: str, token: Token, payload: dict = None) -> dict:
        payload = payload or {}
        if 'from_whom' in payload:
            payload['from'] = payload.pop('from_whom')
        if 'mobile_phone' in payload:
            payload['mobile_phone'] = payload['mobile_phone'].replace(
                "+", "").replace(" ", "")

        status_code, response = await self._async_request(
            method,
            path,
            data=payload,
            headers=token.headers
        )
        logger.debug(
            f"Eskiz request status_code={status_code} body={response}"
        )
        if status_code in [400, 401]:
            raise BadRequest(
                status=response['status'], message=response['message']
            )
        elif status_code == 500:
            if token.auto_update:
                token.update()
                return await self.request(method, path, token, payload)
            raise TokenBlackListed(
                status=response['status'], message=response['message']
            )
        return response

    async def post(self, path: str, token: Token, payload: dict = None):
        return await self.request("POST", path, token, payload)

    async def put(self, path: str, token: Token, payload: dict = None):
        return await self.request("PUT", path, token, payload)

    async def get(self, path: str, token: Token, params: Optional[dict] = None):
        return await self.request("GET", path, token, params)

    async def delete(self, path: str, token: Token, payload: dict = None):
        return await self.request("DELETE", path, token, payload)

    async def patch(self, path: str, token: Token, payload: dict = None):
        return await self.request("PATCH", path, token, payload)


request = Request()
