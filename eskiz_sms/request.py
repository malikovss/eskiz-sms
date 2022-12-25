from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from http.client import responses
from json import JSONDecodeError
from typing import Optional, TYPE_CHECKING, Coroutine
from functools import partial

import httpx

from .enums import Message as ResponseMessage
from .enums import Status as ResponseStatus
from .exceptions import (
    HTTPError,
    BadRequest
)
from .logging import logger

if TYPE_CHECKING:
    from .token import Token

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


class BaseRequest:

    @staticmethod
    def _prepare_request(method: str, path: str, data: dict = None, headers: dict = None):
        return _Request(method, _url(path), data, headers)

    @staticmethod
    def _bad_request(_response: _Response):
        return BadRequest(
            message=_response.data.get('message') or responses[_response.status_code],
            status=_response.data.get('status'),
            status_code=_response.status_code
        )

    def _request(self, _request: _Request):
        try:
            with httpx.Client() as client:
                return self._check_response(client.request(**asdict(_request)))
        except httpx.HTTPError as e:
            raise HTTPError(message=str(e))

    async def _a_request(self, _request: _Request):
        try:
            async with httpx.AsyncClient() as client:
                return self._check_response(await client.request(**asdict(_request)))
        except httpx.HTTPError as e:
            raise HTTPError(message=str(e))

    def _check_response(self, r: httpx.Response) -> _Response:
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


class Request(BaseRequest):
    def __init__(self, is_async=False):
        self._is_async = is_async

    def __call__(self, method: str, path: str, token: Token, payload: dict = None):
        _request = self._prepare_request(
            method,
            path,
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
        response = await self._a_request(_request)
        if response.token_expired and token.auto_update:
            await token.update()
            response = await self._a_request(_request)
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
