import re
from datetime import datetime
from http.client import responses
from json import JSONDecodeError
from typing import Optional, Union

import httpx
from dotenv import get_key, set_key

from .exceptions import (
    DecodeError,
    HTTPError,
    BadRequest
)
from .logging import logger

ESKIZ_TOKEN_KEY = "ESKIZ_TOKEN"
BASE_URL = "https://notify.eskiz.uz/api"
API_VERSION_RE = re.compile("API version: ([0-9.]+)")


def _url(path: str):
    return BASE_URL + path


class Base:

    def _request(self, *, method: str, path: str, data: dict = None, headers: dict = None):
        with httpx.Client() as client:
            response = client.request(
                method=method,
                url=_url(path),
                data=data,
                headers=headers
            )
            return self._check_response(response)

    async def _async_request(self, *, method: str, path: str, data: dict = None, headers: dict = None):
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=_url(path),
                data=data,
                headers=headers
            )
            return self._check_response(response)

    @staticmethod
    def _check_response(response: httpx.Response) -> Union[httpx.Response, dict]:
        if response.status_code not in [200, 201]:
            raise BadRequest(message=responses[response.status_code], status=response.status_code)
        try:
            response.json()
            logger.debug(f"Eskiz request status={response.status_code} body={response.json()}")
        except JSONDecodeError:
            api_version = API_VERSION_RE.search(response.text)
            if api_version:
                return {'api_version': api_version.groups()[0]}
            raise DecodeError("Internal server error")
        except httpx.HTTPError as e:
            raise HTTPError from e
        else:
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
    def headers(self):
        return {
            'Authorization': f'Bearer {self._value}'
        }

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


class Request(Base):
    def __init__(self, is_async=False):
        self.is_async = is_async

    def __call__(self, method: str, path: str, token: Token, payload: dict = None):
        kwargs = dict(
            method=method,
            path=path,
            data=self._prepare_payload(payload),
            headers=token.headers
        )
        if self.is_async:
            return self._async_request(**kwargs)
        return self._request(**kwargs)

    @staticmethod
    def _prepare_payload(payload: dict):
        payload = payload or {}
        if 'from_whom' in payload:
            payload['from'] = payload.pop('from_whom')
        if 'mobile_phone' in payload:
            payload['mobile_phone'] = payload['mobile_phone'].replace("+", "").replace(" ", "")
        return payload

    async def _async_request(self, *, method: str, path: str, data: dict = None, headers: dict = None):
        response = await super()._async_request(method=method, path=path, data=data, headers=headers)

        return response

    def _request(self, *, method: str, path: str, data: dict = None, headers: dict = None):
        response = super()._request(method=method, path=path, data=data, headers=headers)
        return response

    def post(self, path: str, token: Token, payload: dict = None):
        return self("POST", path, token, payload)

    def put(self, path: str, token: Token, payload: dict = None):
        return self("PUT", path, token, payload)

    def get(self, path: str, token: Token, params: Optional[dict] = None):
        return self("GET", path, token, params)

    def delete(self, path: str, token: Token, payload: dict = None):
        return self("DELETE", path, token, payload)

    def patch(self, path: str, token: Token, payload: dict = None):
        return self("PATCH", path, token, payload)


request = Request()
