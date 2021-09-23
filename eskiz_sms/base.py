import json

import requests

from eskiz_sms.consts import ApiPaths, BASE_URL
from eskiz_sms.exceptions import BadRequest, TokenBlackListed
from eskiz_sms.objects import TokenObject, ResponseObject


class Base(object):
    @staticmethod
    def prepare_url(path: str):
        return BASE_URL + path

    @staticmethod
    def to_json(text: str):
        return json.loads(text)


class Token(Base):
    def __init__(self, email: str, password: str):
        self.token = None
        self.headers = None
        self._credentials = dict(email=email, password=password)
        self._get_token()

    def _get_token(self):
        url = self.prepare_url(ApiPaths.GET_TOKEN)
        r = requests.post(url, data=self._credentials)
        response = ResponseObject(**r.json())
        self.token = TokenObject(**response.data).token
        self.headers = {
            'Authorization': f'Bearer {self.token}'
        }

    def update_token(self):
        r = requests.patch(self.prepare_url(ApiPaths.UPDATE_TOKEN), headers=self.headers)
        response = ResponseObject(**r.json())
        self.token = TokenObject(**response.data).token
        return response.message

    def delete_token(self):
        r = requests.delete(self.prepare_url(ApiPaths.DELETE_TOKEN), headers=self.headers)
        response = ResponseObject(**r.json())
        self.token = None
        return response


def __str__(self):
    return self.token


def __repr__(self):
    return self.token


class Request(Base):
    def __init__(self):
        self._recursion = None

    @staticmethod
    def prepare_kwargs(kwargs: dict):
        if 'self' in kwargs:
            kwargs.pop('self')
        return kwargs

    def _make_request(self, method_name: str, path: str, token: Token, payload: dict = None):
        headers = token.headers
        if payload is None:
            payload = {}
        r = requests.request(method_name, self.prepare_url(path), headers=headers, data=payload)
        response: ResponseObject = ResponseObject(**r.json())
        if r.status_code in [400, 401]:
            raise BadRequest(response.message)
        elif r.status_code == 500:
            if not self._recursion:
                self._recursion = True
                token.update_token()
                self._make_request(method_name, path, token)
            else:
                raise TokenBlackListed(response.message)
        else:
            self._recursion = None
            return response

    def post(self, path: str, token: Token, payload: dict = None):
        return self._make_request("POST", path, token, payload)

    def put(self, path: str, token: Token, payload: dict = None):
        return self._make_request("PUT", path, token, payload)

    def get(self, path: str, token: Token, payload: dict = None):
        return self._make_request("GET", path, token, payload)

    def delete(self, path: str, token: Token, payload: dict = None):
        return self._make_request("DELETE", path, token, payload)

    def patch(self, path: str, token: Token, payload: dict = None):
        return self._make_request("PATCH", path, token, payload)


request = Request()
