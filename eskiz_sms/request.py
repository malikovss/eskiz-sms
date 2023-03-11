from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from http.client import responses
from json import JSONDecodeError
from typing import Optional, TYPE_CHECKING

import httpx

from .enums import Message as ResponseMessage
from .enums import Status as ResponseStatus
from .exceptions import (
    HTTPError,
    BadRequest,
    TokenInvalid,
    InvalidCredentials,
)
from .logging import logger

if TYPE_CHECKING:
    from .base import EskizSMSBase

BASE_URL = "https://notify.eskiz.uz/api"
API_VERSION_RE = re.compile("API version: ([0-9.]+)")


# full path
def _url(path: str):
    return BASE_URL + path


@dataclass
class _Response:
    status_code: int
    data: dict
    token_invalid: bool = False


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
    def _exception(_response: _Response):
        status = _response.data.get('status')
        message = _response.data.get('message') or responses[_response.status_code]
        if status == ResponseStatus.TOKEN_INVALID:
            return TokenInvalid(
                message=message,
                status=status,
                status_code=_response.status_code
            )
        if message == ResponseMessage.INVALID_CREDENTIALS:
            return InvalidCredentials(message="Invalid credentials", status_code=_response.status_code)
        return BadRequest(
            message=message,
            status=status,
            status_code=_response.status_code
        )

    @staticmethod
    def _get_authorization_header(token):
        return {
            "Authorization": f"Bearer {token}"
        }

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
            if r.status_code == 200:
                api_version = API_VERSION_RE.search(r.text)
                if api_version:
                    response = _Response(status_code=r.status_code, data={'api_version': api_version.groups()[0]})

        if response is None:
            response = _Response(status_code=r.status_code, data={'message': responses[r.status_code]})

        logger.debug(f"Eskiz request status_code={response.status_code} body={response.data}")

        if response.status_code == 401:
            if response.data.get('status') == ResponseStatus.TOKEN_INVALID:
                response.token_invalid = True
                return response

        if response.status_code not in [200, 201]:
            raise self._exception(response)

        return response


class Request(BaseRequest):
    def __init__(self, eskiz: EskizSMSBase):
        self._eskiz = eskiz

    def __call__(self, method: str, path: str, payload: dict = None):
        _request = self._prepare_request(
            method,
            path,
            data=self._prepare_payload(payload)
        )
        if getattr(self._eskiz, 'is_async', False):  # noqa
            return self.async_request(_request)
        return self.request(_request)

    async def async_request(self, _request: _Request) -> dict:
        _request.headers = self._get_authorization_header(await self._eskiz.token.get())
        response = await self._a_request(_request)
        if response.token_invalid and self._eskiz.token.auto_update:
            logger.debug("Refreshing the token")
            _request.headers = self._get_authorization_header(await self._eskiz.token.get(get_new=True))
            response = await self._a_request(_request)
        if response.status_code not in [200, 201]:
            raise self._exception(response)
        return response.data

    def request(self, _request: _Request) -> dict:
        _request.headers = self._get_authorization_header(self._eskiz.token.get())
        response = self._request(_request)
        if response.token_invalid and self._eskiz.token.auto_update:
            logger.debug("Refreshing the token")
            _request.headers = self._get_authorization_header(self._eskiz.token.get(get_new=True))
            response = self._request(_request)
        if response.status_code not in [200, 201]:
            raise self._exception(response)
        return response.data

    @staticmethod
    def _prepare_payload(payload: dict):
        payload = payload or {}
        if 'from_whom' in payload:
            payload['from'] = payload.pop('from_whom')
        if 'mobile_phone' in payload:
            payload['mobile_phone'] = payload['mobile_phone'].replace("+", "").replace(" ", "")
        return payload

    def post(self, path: str, payload: dict = None):
        return self("POST", path, payload)

    def put(self, path: str, payload: dict = None):
        return self("PUT", path, payload)

    def get(self, path: str, payload: Optional[dict] = None):
        return self("GET", path, payload)

    def delete(self, path: str, payload: dict = None):
        return self("DELETE", path, payload)

    def patch(self, path: str, payload: dict = None):
        return self("PATCH", path, payload)
