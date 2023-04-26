import re
from typing import Optional, List

from .exceptions import ContactNotFound, InvalidCallbackUrl
from .http import EskizHttpClient
from .logging import logger
from .token import Token
from .types import User, Contact, Response, ContactCreated, HttpRequest


class EskizSMS:
    __slots__ = (
        "token",
        "_user",
        "callback_url",
        "http_client",
    )

    def __init__(
            self,
            email: str,
            password: str,
            callback_url: str = None,
            save_token: bool = False,
            env_file_path: str = None,
            auto_update_token=True,
            http_client=EskizHttpClient()
    ):

        if callback_url is not None:
            self._validate_callback_url(callback_url)
        self.callback_url = callback_url

        self.token = Token(
            self,
            email,
            password,
            save_token=save_token,
            env_file_path=env_file_path,
            auto_update=auto_update_token,
        )
        self.http_client = http_client
        self._user: Optional[User] = None

    def __call__(self, method: str, path: str, payload: dict = None, is_async=False):
        request_data = HttpRequest(
            method,
            path,
            data=self.prepare_payload(payload)
        )
        if is_async:
            return self.arequest(request_data)
        return self.request(request_data)

    def headers(self, token: str):
        return {
            "Authorization": "Bearer %s" % token
        }

    async def arequest(self, request_data: HttpRequest) -> dict:
        request_data.headers = self.headers(await self.token.get(is_async=True))
        response = await self.http_client.arequest(request_data)
        if response.token_invalid and self.token.auto_update:
            logger.debug("Refreshing the token")
            request_data.headers = self.headers(
                await self.token.get(get_new=True, is_async=True)
            )
            response = await self.http_client.arequest(request_data)
        if response.status_code not in [200, 201]:
            raise self.http_client.exception(response)
        return response.data

    def request(self, request_data: HttpRequest) -> dict:
        request_data.headers = self.headers(self.token.get())
        response = self.http_client.request(request_data)
        if response.token_invalid and self.token.auto_update:
            logger.debug("Refreshing the token")
            request_data.headers = self.headers(self.token.get(get_new=True))
            response = self.http_client.request(request_data)
        if response.status_code not in [200, 201]:
            raise self.http_client.exception(response)
        return response.data

    @staticmethod
    def prepare_payload(payload: dict):
        payload = payload or {}
        if 'from_whom' in payload:
            payload['from'] = payload.pop('from_whom')
        if 'mobile_phone' in payload:
            payload['mobile_phone'] = payload['mobile_phone'].replace("+", "").replace(" ", "")
        return {k: v for k, v in payload.items() if v}

    def post(self, path: str, payload: dict = None, is_async=False):
        return self("POST", path, payload, is_async)

    def put(self, path: str, payload: dict = None, is_async=False):
        return self("PUT", path, payload, is_async)

    def get(self, path: str, payload: Optional[dict] = None, is_async=False):
        return self("GET", path, payload, is_async)

    def delete(self, path: str, payload: dict = None, is_async=False):
        return self("DELETE", path, payload, is_async)

    def patch(self, path: str, payload: dict = None, is_async=False):
        return self("PATCH", path, payload, is_async)

    @staticmethod
    def _validate_callback_url(url):
        if url_validator(url) is False:
            raise InvalidCallbackUrl(message="Invalid callback url")

    def _get_callback_url(self, callback_url: str = None):
        if callback_url is not None:
            self._validate_callback_url(callback_url)
            return callback_url
        return self.callback_url

    @property
    def user(self) -> Optional[User]:
        if self._user is None:
            self._user = self._user_data()
        return self._user

    def _user_data(self) -> Optional[User]:
        response = self.get("/auth/user")
        return User(**response)

    def add_contact(self, name: str, email: str, group: str, mobile_phone: str) -> ContactCreated:
        response = self.post(
            "/contact",
            payload={
                "name": name,
                "email": email,
                "group": group,
                "mobile_phone": str(mobile_phone),
            })
        return ContactCreated(response['data'])

    def update_contact(self, contact_id: int, name: str, group: str, mobile_phone: str) -> Optional[Contact]:
        response = self.put(
            f"/contact/{contact_id}",
            payload={
                "name": name,
                "group": group,
                "mobile_phone": str(mobile_phone),
            })
        if response and isinstance(response, list):
            return Contact(**response[0])

    def get_contact(self, contact_id: int, raise_exception=False) -> Optional[Contact]:
        response = self.get(f"/contact/{contact_id}")
        if not response:
            if raise_exception:
                raise ContactNotFound
            return None
        return Contact(**response[0])

    def delete_contact(self, contact_id: int) -> Response:
        response = self.delete(f"/contact/{contact_id}")
        return Response(**response)

    def send_sms(self, mobile_phone: str, message: str, from_whom: str = '4546',
                 callback_url: str = None) -> Response:
        """
        :param mobile_phone: Phone number without plus sign
        :param message: Message to send
        :param from_whom: To use a nickname, you need to change the field to your own
        :param callback_url: This is an optional field that is used to automatically receive SMS status from the server.
            Specify the callback URL where you will receive POST data in the following format:
            {"message_id": "4385062", "user_sms_id": "your_id_here", "country": "UZ",
            "phone_number": "998991234567", "sms_count": "1",
            "status" : "DELIVER", "status_date": "2021-04-02 00:39:36"}
        :return: Response
        """
        payload = {
            "mobile_phone": str(mobile_phone),
            "message": message,
            "from_whom": from_whom,
            "callback_url": self._get_callback_url(callback_url)
        }
        return Response(**self.post("/message/sms/send", payload=payload))

    def send_global_sms(self, mobile_phone: str, message: str, country_code: str,
                        callback_url: str = None, unicode: str = "0") -> Response:
        """
        :param mobile_phone: Phone number without plus sign
        :param message: Message to send
        :param country_code: e.g. 'US'
        :param callback_url: Pass a callback url to get notified when the message is sent
        :param unicode: Default is 0, pass 1 if you want to send cyrillic message
        :return:
        """
        payload = {
            "mobile_phone": str(mobile_phone),
            "message": message,
            "country_code": country_code,
            "unicode": unicode,
            "callback_url": self._get_callback_url(callback_url)
        }
        return Response(**self.post("/message/sms/send-global", payload=payload))

    def send_batch(self, *, messages: List[dict], from_whom: str = "4546", dispatch_id: int) -> Response:
        """
        :param messages: List of messages to send.
            [{"user_sms_id":"sms1","to": 998998046210, "text": "eto test"}]
        :param from_whom: 4546
        :param dispatch_id:
        :returns: Response
        :rtype: eskiz_sms.types.Response
        """
        return Response(**self.post(
            "/message/sms/send-batch",
            payload={
                "messages": [
                    {
                        "user_sms_id": message["user_sms_id"],
                        "to": str(message["to"]),
                        "text": message["text"]
                    } for message in messages
                ],
                "from_whom": from_whom,
                "dispatch_id": dispatch_id
            }))

    def get_user_messages(self, from_date: str, to_date: str) -> Response:
        return Response(**self.get(
            "/message/sms/get-user-messages",
            payload={
                "from_date": from_date,
                "to_date": to_date,
                "user_id": self.user.id
            }
        ))

    def get_user_messages_by_dispatch(self, dispatch_id: int) -> Response:
        return Response(**self.get(
            "/message/sms/get-user-messages-by-dispatch",
            payload={
                "dispatch_id": dispatch_id,
                "user_id": self.user.id
            }))

    def get_dispatch_status(self, dispatch_id: int) -> Response:
        return Response(**self.get(
            "/message/sms/get-dispatch-status",
            payload={
                "dispatch_id": dispatch_id,
                "user_id": self.user.id
            }))

    def create_template(self, name: str, text: str) -> Response:
        return Response(**self.post(
            "/template",
            payload={
                "name": name,
                "text": text,
            }))

    def update_template(self, template_id: int, name: str, text: str) -> Response:
        return Response(**self.put(
            f"/template/{template_id}",
            payload={
                "name": name,
                "text": text,
            }
        ))

    def get_template(self, template_id: int) -> Response:
        return Response(**self.get(f"/template/{template_id}"))

    def get_templates(self) -> Response:
        return Response(**self.get("/template"))

    def totals(self, year: int) -> Response:
        return Response(**self.post(
            "/user/totals",
            payload={
                "year": year,
                "user_id": self.user.id
            }))

    def get_limit(self) -> Response:
        return Response(**self.get("/user/get-limit"))

    def close(self):
        self.http_client.close()

    # ===Async functions=== #
    @property
    async def auser(self) -> Optional[User]:
        if self._user is None:
            self._user = await self._auser_data()
        return self._user

    async def _auser_data(self) -> Optional[User]:
        response = await self.get("/auth/user", is_async=True)
        return User(**response)

    async def aadd_contact(self, name: str, email: str, group: str, mobile_phone: str) -> ContactCreated:
        response = await self.post(
            "/contact",
            payload={
                "name": name,
                "email": email,
                "group": group,
                "mobile_phone": str(mobile_phone),
            }, is_async=True)
        return ContactCreated(response['data'])

    async def aupdate_contact(self, contact_id: int, name: str, group: str, mobile_phone: str) -> Optional[Contact]:
        response = await self.put(
            f"/contact/{contact_id}",
            payload={
                "name": name,
                "group": group,
                "mobile_phone": str(mobile_phone),
            }, is_async=True)
        if response and isinstance(response, list):
            return Contact(**response[0])

    async def aget_contact(self, contact_id: int, raise_exception=False) -> Optional[Contact]:
        response = await self.get(f"/contact/{contact_id}", is_async=True)
        if not response:
            if raise_exception:
                raise ContactNotFound
            return None
        return Contact(**response[0])

    async def adelete_contact(self, contact_id: int) -> Response:
        response = await self.delete(f"/contact/{contact_id}", is_async=True)
        return Response(**response)

    async def asend_sms(self, mobile_phone: str, message: str, from_whom: str = '4546',
                        callback_url: str = None) -> Response:
        """
        :param mobile_phone: Phone number without plus sign
        :param message: Message to send
        :param from_whom: To use a nickname, you need to change the field to your own
        :param callback_url: This is an optional field that is used to automatically receive SMS status from the server.
            Specify the callback URL where you will receive POST data in the following format:
            {"message_id": "4385062", "user_sms_id": "your_id_here", "country": "UZ",
            "phone_number": "998991234567", "sms_count": "1",
            "status" : "DELIVER", "status_date": "2021-04-02 00:39:36"}
        :return: Response
        """
        payload = {
            "mobile_phone": str(mobile_phone),
            "message": message,
            "from_whom": from_whom,
            "callback_url": self._get_callback_url(callback_url)
        }
        response = await self.post("/message/sms/send", payload=payload, is_async=True)
        return Response(**response)

    async def asend_global_sms(self, mobile_phone: str, message: str, country_code: str,
                               callback_url: str = None, unicode: str = "0") -> Response:
        """
        :param mobile_phone: Phone number without plus sign
        :param message: Message to send
        :param country_code: e.g. 'US'
        :param callback_url: Pass a callback url to get notified when the message is sent
        :param unicode: Default is 0, pass 1 if you want to send cyrillic message
        :return:
        """
        payload = {
            "mobile_phone": str(mobile_phone),
            "message": message,
            "country_code": country_code,
            "unicode": unicode,
            "callback_url": self._get_callback_url(callback_url)
        }
        response = await self.post("/message/sms/send-global", payload=payload, is_async=True)
        return Response(**response)

    async def asend_batch(self, *, messages: List[dict], from_whom: str = "4546", dispatch_id: int) -> Response:
        """
        :param messages: List of messages to send.
            [{"user_sms_id":"sms1","to": 998998046210, "text": "eto test"}]
        :param from_whom: 4546
        :param dispatch_id:
        :returns: Response
        :rtype: eskiz_sms.types.Response
        """
        response = await self.post(
            "/message/sms/send-batch",
            payload={
                "messages": [
                    {
                        "user_sms_id": message["user_sms_id"],
                        "to": str(message["to"]),
                        "text": message["text"]
                    } for message in messages
                ],
                "from_whom": from_whom,
                "dispatch_id": dispatch_id
            }, is_async=True)
        return Response(**response)

    async def aget_user_messages(self, from_date: str, to_date: str) -> Response:
        user = await self.auser
        response = await self.get(
            "/message/sms/get-user-messages",
            payload={
                "from_date": from_date,
                "to_date": to_date,
                "user_id": user.id
            },
            is_async=True
        )
        return Response(**response)

    async def aget_user_messages_by_dispatch(self, dispatch_id: int) -> Response:
        user = await self.auser
        response = await self.get(
            "/message/sms/get-user-messages-by-dispatch",
            payload={
                "dispatch_id": dispatch_id,
                "user_id": user.id
            }, is_async=True)
        return Response(**response)

    async def aget_dispatch_status(self, dispatch_id: int) -> Response:
        user = await self.auser
        response = self.get(
            "/message/sms/get-dispatch-status",
            payload={
                "dispatch_id": dispatch_id,
                "user_id": user.id
            }, is_async=True)
        return Response(**response)

    async def acreate_template(self, name: str, text: str) -> Response:
        response = await self.post(
            "/template",
            payload={
                "name": name,
                "text": text,
            }, is_async=True)
        return Response(**response)

    async def aupdate_template(self, template_id: int, name: str, text: str) -> Response:
        response = await self.put(
            f"/template/{template_id}",
            payload={
                "name": name,
                "text": text,
            }, is_async=True
        )
        return Response(**response)

    async def aget_template(self, template_id: int) -> Response:
        response = await self.get(f"/template/{template_id}", is_async=True)
        return Response(**response)

    async def aget_templates(self) -> Response:
        response = await self.get("/template", is_async=True)
        return Response(**response)

    async def atotals(self, year: int) -> Response:
        user = await self.auser
        response = await self.post(
            "/user/totals",
            payload={
                "year": year,
                "user_id": user.id
            }, is_async=True)
        return Response(**response)

    async def aget_limit(self) -> Response:
        response = await self.get("/user/get-limit", is_async=True)
        return Response(**response)

    async def aclose(self):
        await self.http_client.aclose()


URL_RE = re.compile(
    r"[(http(s)?):\/\/(www\.)?a-zA-Z0-9@:%._\+~#=]"  # noqa
    r"{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)"  # noqa
)


def url_validator(url: str):
    return bool(URL_RE.search(url))
