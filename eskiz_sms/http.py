from __future__ import annotations

import re
from contextlib import contextmanager, asynccontextmanager
from dataclasses import asdict
from http.client import responses
from json import JSONDecodeError
from typing import Optional, TYPE_CHECKING, Dict

import httpx

from .enums import Message as ResponseMessage
from .enums import Status as ResponseStatus
from .exceptions import (
    HTTPError, TokenInvalid, InvalidCredentials, BadRequest,
)
from .logging import logger
from .types import HttpRequest, HttpResponse

if TYPE_CHECKING:
    pass

API_VERSION_RE = re.compile("API version: ([0-9.]+)")


class EskizHttpClient:
    BASE_URL = "https://notify.eskiz.uz/api"

    def __init__(
            self,
            pool_connections: bool = True,
            event_hooks: Optional[Dict[str, object]] = None,
            timeout: float = 5,
            proxies: Optional[Dict[str, str]] = None,
            retries: int = 0,
    ):
        self.pool_connections = pool_connections
        self.event_hooks = event_hooks
        self.timeout = timeout
        self.proxies = proxies
        self.retries = retries
        self._client: Optional[httpx.Client] = None
        self._aclient: Optional[httpx.AsyncClient] = None
        self._transport: Optional[httpx.HTTPTransport] = None
        self._atransport: Optional[httpx.AsyncHTTPTransport] = None

    @contextmanager
    def client(self) -> httpx.Client:
        if self._transport is None:
            self._transport = httpx.HTTPTransport(
                retries=self.retries
            )
        if self._client and self._client.is_closed:
            self._client = None
        client = self._client or httpx.Client(
            base_url=self.BASE_URL,
            proxies=self.proxies,
            timeout=self.timeout,
            transport=self._transport
        )
        try:
            yield client
        finally:
            if self.pool_connections:
                if self._client is None or self._client.is_closed:
                    self._client = client
            else:
                client.close()

    @asynccontextmanager
    async def aclient(self) -> httpx.AsyncClient:
        if self._atransport is None:
            self._atransport = httpx.AsyncHTTPTransport(
                retries=self.retries
            )
        if self._aclient and self._aclient.is_closed:
            self._aclient = None
        client = self._aclient or httpx.AsyncClient(
            base_url=self.BASE_URL,
            proxies=self.proxies,
            timeout=self.timeout,
            transport=self._atransport
        )
        try:
            yield client
        finally:
            if self.pool_connections:
                if self._client is None or self._client.is_closed:
                    self._client = client
            else:
                await client.aclose()

    def request(self, _request: HttpRequest):
        try:
            with self.client() as client:
                return self._check_response(client.request(**asdict(_request)))
        except httpx.HTTPError as e:
            raise HTTPError(message=str(e))

    async def arequest(self, _request: HttpRequest):
        try:
            async with self.aclient() as client:
                return self._check_response(await client.request(**asdict(_request)))
        except httpx.HTTPError as e:
            raise HTTPError(message=str(e))

    def _check_response(self, r: httpx.Response) -> HttpResponse:
        response: Optional[HttpResponse] = None
        try:
            response = HttpResponse(status_code=r.status_code, data=r.json())
        except JSONDecodeError:
            if r.status_code == 200:
                api_version = API_VERSION_RE.search(r.text)
                if api_version:
                    response = HttpResponse(status_code=r.status_code, data={'api_version': api_version.groups()[0]})

        if response is None:
            response = HttpResponse(status_code=r.status_code, data={'message': responses[r.status_code]})

        logger.debug(f"Eskiz request status_code={response.status_code} body={response.data}")

        if response.status_code == 401:
            if response.data.get('status') == ResponseStatus.TOKEN_INVALID:
                response.token_invalid = True
                return response

        if response.status_code not in [200, 201]:
            raise self.exception(response)

        return response

    @staticmethod
    def exception(response_data: HttpResponse):
        status = response_data.data.get('status')
        message = response_data.data.get('message') or responses[response_data.status_code]
        if status == ResponseStatus.TOKEN_INVALID:
            return TokenInvalid(
                message=message,
                status=status,
                status_code=response_data.status_code
            )
        if message == ResponseMessage.INVALID_CREDENTIALS:
            return InvalidCredentials(message="Invalid credentials", status_code=response_data.status_code)
        return BadRequest(
            message=message,
            status=status,
            status_code=response_data.status_code
        )

    def close(self):
        if self._client:
            self._client.close()

    async def aclose(self):
        if self._aclient:
            await self._aclient.aclose()
