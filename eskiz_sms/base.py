import re
from dataclasses import dataclass, asdict
from datetime import datetime
from http.client import responses
from json import JSONDecodeError
from typing import Optional

import httpx
from dotenv import get_key, set_key

from .enums import Message as ResponseMessage
from .enums import Status as ResponseStatus
from .exceptions import (
    HTTPError,
    BadRequest
)
from .logging import logger

ESKIZ_TOKEN_KEY = "ESKIZ_TOKEN"
BASE_URL = "https://notify.eskiz.uz/api"
API_VERSION_RE = re.compile("API version: ([0-9.]+)")


def _url(path: str):
    return BASE_URL + path


@dataclass
class _Response:
    status_code: int
    data: dict
    token_expired: bool = False


@dataclass
class _Request:
    method: str
    url: str
    data: dict = None
    headers: dict = None


class Base:

    @staticmethod
    def _bad_request(_response: _Response):
        return BadRequest(
            message=_response.data.get('message') or responses[_response.status_code],
            status=_response.status_code
        )

    def _request(self, _request: _Request):
        try:
            with httpx.Client() as client:
                return self.__check_response(client.request(**asdict(_request)))
        except httpx.HTTPError as e:
            raise HTTPError from e

    async def _async_request(self, _request: _Request):
        try:
            async with httpx.AsyncClient() as client:
                return self.__check_response(await client.request(**asdict(_request)))
        except httpx.HTTPError as e:
            raise HTTPError from e

    def __check_response(self, r: httpx.Response) -> _Response:
        response: Optional[_Response] = None
        try:
            response = _Response(status_code=r.status_code, data=r.json())
        except JSONDecodeError:
            if response.status_code == 200:
                api_version = API_VERSION_RE.search(r.text)
                if api_version:
                    response = _Response(status_code=r.status_code, data={'api_version': api_version.groups()[0]})

        if response is None:
            response = _Response(status_code=r.status_code, data={'message': responses[r.status_code]})

        logger.debug(f"Eskiz request status_code={response.status_code} body={response.data}")

        if response.status_code == 401:
            if response.data.get('status') == ResponseStatus.TOKEN_INVALID:
                if response.data.get('message') == ResponseMessage.EXPIRED_TOKEN:
                    response.token_expired = True
                    return response

        if response.status_code not in [200, 201]:
            raise self._bad_request(response)

        return response


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


class Request(Base):
    def __init__(self, is_async=False):
        self._is_async = is_async

    def __call__(self, method: str, path: str, token: Token, payload: dict = None):
        _request = _Request(
            method=method,
            url=_url(path),
            data=self._prepare_payload(payload)
        )

        if self._is_async:
            return self.async_request(_request, token)
        return self.request(_request, token)

    async def async_request(self, _request: _Request, token: Token) -> dict:
        _token_value = await token.get()
        _request.headers = {
            "Authorization": f"Bearer {_token_value}"
        }
        response = await self._async_request(_request)
        if response.token_expired and token.auto_update:
            await token.update()
            response = await self._async_request(_request)
        if response.status_code not in [200, 201]:
            raise self._bad_request(response)
        return response.data

    def request(self, _request: _Request, token: Token) -> dict:
        _token_value = token.get()
        _request.headers = {
            "Authorization": f"Bearer {_token_value}"
        }
        response = self._request(_request)
        if response.token_expired and token.auto_update:
            token.update()
            response = self._request(_request)
        if response.status_code not in [200, 201]:
            raise self._bad_request(response)
        return response.data

    @staticmethod
    def _prepare_payload(payload: dict):
        payload = payload or {}
        if 'from_whom' in payload:
            payload['from'] = payload.pop('from_whom')
        if 'mobile_phone' in payload:
            payload['mobile_phone'] = payload['mobile_phone'].replace("+", "").replace(" ", "")
        return payload

    def post(self, path: str, token: Token, payload: dict = None):
        return self("POST", path, token, payload)

    def put(self, path: str, token: Token, payload: dict = None):
        return self("PUT", path, token, payload)

    def get(self, path: str, token: Token, payload: Optional[dict] = None):
        return self("GET", path, token, payload)

    def delete(self, path: str, token: Token, payload: dict = None):
        return self("DELETE", path, token, payload)

    def patch(self, path: str, token: Token, payload: dict = None):
        return self("PATCH", path, token, payload)


request = Request()
