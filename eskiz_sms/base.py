import json
from datetime import datetime
from json import JSONDecodeError
from typing import Optional

import requests
from dotenv import get_key, set_key

from eskiz_sms.exceptions import (
    BadRequest,
    TokenBlackListed,
    TokenInvalid,
    InvalidCredentials, EskizException
)
from eskiz_sms.types import Response

ESKIZ_TOKEN_KEY = "ESKIZ_TOKEN"


class Base:
    BASE_URL = "https://notify.eskiz.uz/api"

    def _make_url(self, path: str):
        return self.BASE_URL + path

    @staticmethod
    def to_json(text: str):
        return json.loads(text)


class Token(Base):
    __slots__ = (
        "auto_update",
        "save_token",
        "env_file_path",
        "_token",
        "_credentials",
    )

    def __init__(self, email: str, password: str, save_token=False, env_file_path=None, auto_update: bool = True):
        self.auto_update = auto_update
        self.save_token = save_token

        self._token = None
        self._credentials = dict(email=email, password=password)

        if save_token:
            if env_file_path is None:
                env_file_path = '.env'
            self.env_file_path = env_file_path

        self.__last_updated_at: Optional[datetime] = None

    @property
    def token(self):
        try:
            if self._token is None:
                if self.save_token:
                    _token = self._get_token()
                    if not _token:
                        _token = self._get_new_token()
                        self._save_token(_token)
                    else:
                        try:
                            self._check_token(_token)
                        except TokenInvalid:
                            _token = self._get_new_token()
                            self._save_token(_token)
                    self._token = _token
                else:
                    self._token = self._get_new_token()
            return self._token
        except EskizException as e:
            raise e

    @token.setter
    def token(self, value):
        self._token = value

    def set(self, value):
        self.token = value

    @property
    def headers(self):
        return {
            'Authorization': f'Bearer {self.token}'
        }

    def update(self):
        if self.__last_updated_at and (self.__last_updated_at - datetime.now()).days < 20:
            # It's for being sure that token isn't updating too fast. To avoid recursion.
            raise EskizException(message="Can't update too fast")
        else:
            try:
                self._check_token(self.token)
                self.__last_updated_at = datetime.now()
            except requests.exceptions.RequestException as e:
                raise EskizException from e

    def _check_token(self, _token: str):
        _headers = {
            'Authorization': f'Bearer {_token}'
        }
        r = requests.patch(self._make_url("/auth/refresh"), headers=_headers)
        if r.status_code == 401:
            response = Response(**r.json())
            raise TokenInvalid(status=response.status, message=response.message)

    def _save_token(self, _token):
        set_key(self.env_file_path, key_to_set=ESKIZ_TOKEN_KEY, value_to_set=_token)
        return _token

    def _get_token(self):
        return get_key(dotenv_path=self.env_file_path, key_to_get=ESKIZ_TOKEN_KEY)

    def _get_new_token(self):
        r = requests.post(self._make_url("/auth/login"), data=self._credentials)
        response = Response(**r.json())
        if r.status_code == 401:
            raise InvalidCredentials(response.message)
        elif r.status_code != 200:
            raise BadRequest(response.message)
        return response.data.get('token')

    def __repr__(self):
        return self.token

    def __str__(self):
        return self.__repr__()


class Request(Base):

    def _make_request(self, method_name: str, path: str, token: Token, payload: dict = None) -> Response:
        payload = payload or {}
        if 'from_whom' in payload:
            payload['from'] = payload.pop('from_whom')
        if 'mobile_phone' in payload:
            payload['mobile_phone'] = payload['mobile_phone'].replace("+", "").replace(" ", "")

        r = requests.request(
            method=method_name,
            url=self._make_url(path),
            data=payload,
            headers=token.headers
        )
        try:
            r_json = r.json()
        except JSONDecodeError:
            raise EskizException("Internal server error")
        if 'message' in r_json or 'status' in r_json:
            response = Response(**r_json)
        else:
            response = Response(data=r_json)
        if r.status_code in [400, 401]:
            raise BadRequest(status=response.status, message=response.message)
        elif r.status_code == 500:
            if token.auto_update:
                try:
                    token.update()
                    return self._make_request(method_name, path, token, payload)
                except EskizException as e:
                    raise e
            raise TokenBlackListed(status=response.status, message=response.message)
        return response

    def post(self, path: str, token: Token, payload: dict = None):
        return self._make_request("POST", path, token, payload)

    def put(self, path: str, token: Token, payload: dict = None):
        return self._make_request("PUT", path, token, payload)

    def get(self, path: str, token: Token, params: Optional[dict] = None):
        return self._make_request("GET", path, token, params)

    def delete(self, path: str, token: Token, payload: dict = None):
        return self._make_request("DELETE", path, token, payload)

    def patch(self, path: str, token: Token, payload: dict = None):
        return self._make_request("PATCH", path, token, payload)


request = Request()
