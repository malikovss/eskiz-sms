import json
import logging
from typing import Optional

import requests

from eskiz_sms.exceptions import BadRequest, TokenBlackListed, UpdateRetryCountExceeded
from eskiz_sms.types import Response

logger = logging.getLogger("eskiz_sms")


class Base:
    BASE_URL = "https://notify.eskiz.uz/api"

    def _make_url(self, path: str):
        return self.BASE_URL + path

    @staticmethod
    def to_json(text: str):
        return json.loads(text)


class Token(Base):
    __slots__ = (
        "auto_update"
        "update_retry_count"
        "_retry_count"
        "_token"
        "_credentials"
    )

    def __init__(self, email: str, password: str, auto_update: bool = True, update_retry_count: int = 3):
        self.auto_update = auto_update
        self.update_retry_count = update_retry_count
        self._retry_count = 0

        self._token = None
        self._credentials = dict(email=email, password=password)

    @property
    def token(self):
        if self._token is None:
            _response = self._get()
            self._token = _response.data.get('token')
        return self._token

    @token.setter
    def token(self, value):
        self._token = value

    @property
    def headers(self):
        return {
            'Authorization': f'Bearer {self.token}'
        }

    def _get(self):
        url = self._make_url("/auth/login")
        r = requests.post(url, data=self._credentials)
        response = Response(**r.json())
        return response

    def update(self):
        if self._retry_count == self.update_retry_count:
            raise UpdateRetryCountExceeded
        r = requests.patch(self._make_url("/auth/refresh"), headers=self.headers)
        response = Response(**r.json())
        self.token = response.data.get('token')
        self._retry_count += 1
        return response.message

    def delete(self):
        r = requests.delete(self._make_url("/auth/invalidate"), headers=self.headers)
        response = Response(**r.json())
        self.token = None
        return response

    def revoke_retry_count(self):
        self._retry_count = 0

    def __str__(self):
        return self.token

    def __repr__(self):
        return self.token


class Request(Base):

    def _make_request(self, method_name: str, path: str, token: Token, payload: dict = None) -> Response:
        if payload is not None:
            if payload.get('from_whom', None):
                payload['from'] = payload.pop('from_whom')
            if 'self' in payload:
                payload.pop('self')

        kwargs = {
            'method': method_name,
            'url': self._make_url(path),
            'headers': token.headers
        }
        if method_name == "GET":
            kwargs['params'] = payload
        else:
            kwargs['json'] = payload

        r = requests.request(**kwargs)
        response = Response(**r.json())
        if r.status_code in [400, 401]:
            raise BadRequest(response.message)
        elif r.status_code == 500:
            if token.auto_update:
                try:
                    token.update()
                except UpdateRetryCountExceeded:
                    raise TokenBlackListed(response.message)
                else:
                    token.revoke_retry_count()
                    return self._make_request(method_name, path, token, payload)
            else:
                raise TokenBlackListed(response.message)
        else:
            logger.info(response)
            return response

    def post(self, path: str, token: Token, payload: Optional[dict] = None):
        return self._make_request("POST", path, token, payload)

    def put(self, path: str, token: Token, payload: Optional[dict] = None):
        return self._make_request("PUT", path, token, payload)

    def get(self, path: str, token: Token, params: Optional[dict] = None):
        return self._make_request("GET", path, token, params)

    def delete(self, path: str, token: Token, payload: Optional[dict] = None):
        return self._make_request("DELETE", path, token, payload)

    def patch(self, path: str, token: Token, payload: Optional[dict] = None):
        return self._make_request("PATCH", path, token, payload)


request = Request()
