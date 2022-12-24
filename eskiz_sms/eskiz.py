from typing import Optional, List

from .base import Token, Request
from .exceptions import ContactNotFound
from .types import User, Contact, Response


class EskizSMS:
    __slots__ = (
        "token",
        "_user",
        "_request",
        "callback_url"
    )

    def __init__(
            self,
            email: str,
            password: str,
            callback_url: str = None,
            save_token: bool = False,
            env_file_path: str = None,
            auto_update_token=True,
            is_async=False
    ):
        self.token = Token(
            email,
            password,
            save_token=save_token,
            env_file_path=env_file_path,
            auto_update=auto_update_token,
            is_async=is_async
        )
        self._request = Request(is_async)
        self._user: Optional[User] = None
        self.callback_url = callback_url
        if self.callback_url:
            pass

    @property
    def user(self) -> Optional[User]:
        self._user = self._user_data()
        return self._user

    def _user_data(self):
        return User(
            **self._request.get(
                "/auth/user",
                token=self.token
            )
        )

    def add_contact(self, name: str, email: str, group: str, mobile_phone: str) -> int:
        response = self._request.post(
            "/contact",
            token=self.token,
            payload={
                "name": name,
                "email": email,
                "group": group,
                "mobile_phone": str(mobile_phone),
            })
        return response['data']['contact_id']

    def update_contact(self, contact_id: int, name: str, group: str, mobile_phone: str) -> Optional[Contact]:
        response = self._request.put(
            f"/contact/{contact_id}",
            token=self.token,
            payload={
                "name": name,
                "group": group,
                "mobile_phone": str(mobile_phone),
            })
        if response and isinstance(response, list):
            return Contact(**response[0])

    def get_contact(self, contact_id: int, raise_exception=False) -> Optional[Contact]:
        response = self._request.get(f"/contact/{contact_id}", token=self.token)
        if not response:
            if raise_exception:
                raise ContactNotFound
            return None
        return Contact(**response[0])

    def delete_contact(self, contact_id: int) -> Response:
        response = self._request.delete(f"/contact/{contact_id}", token=self.token)
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
        }
        callback_url = callback_url or self.callback_url
        if callback_url:
            pass
        return Response(**self._request.post("/message/sms/send", token=self.token, payload=payload))

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
            "unicode": unicode
        }
        callback_url = callback_url or self.callback_url
        if callback_url:
            pass
        return Response(**self._request.post("/message/sms/send-global", token=self.token, payload=payload))

    def send_batch(self, *, messages: List[dict], from_whom: str = "4546", dispatch_id: int) -> Response:
        """
        :param messages: List of messages to send.
            [{"user_sms_id":"sms1","to": 998998046210, "text": "eto test"}]
        :param from_whom: 4546
        :param dispatch_id:
        :returns: Response
        :rtype: eskiz_sms.types.Response
        """
        return Response(**self._request.post(
            "/message/sms/send-batch",
            token=self.token,
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
        return Response(**self._request.get(
            "/message/sms/get-user-messages",
            token=self.token,
            payload={
                "from_date": from_date,
                "to_date": to_date,
                "user_id": self.user.id
            }
        ))

    def get_user_messages_by_dispatch(self, dispatch_id: int) -> Response:
        return Response(**self._request.get(
            "/message/sms/get-user-messages-by-dispatch",
            token=self.token,
            payload={
                "dispatch_id": dispatch_id,
                "user_id": self.user.id
            }))

    def get_dispatch_status(self, dispatch_id: int) -> Response:
        return Response(**self._request.get(
            "/message/sms/get-dispatch-status",
            token=self.token,
            payload={
                "dispatch_id": dispatch_id,
                "user_id": self.user.id
            }))

    def create_template(self, name: str, text: str) -> Response:
        return Response(**self._request.post(
            "/template",
            token=self.token,
            payload={
                "name": name,
                "text": text,
            }))

    def update_template(self, template_id: int, name: str, text: str) -> Response:
        return Response(**self._request.put(
            f"/template/{template_id}",
            token=self.token,
            payload={
                "name": name,
                "text": text,
            }
        ))

    def get_template(self, template_id: int) -> Response:
        return Response(**self._request.get(f"/template/{template_id}", token=self.token))

    def get_templates(self) -> Response:
        return Response(**self._request.get("/template", token=self.token))

    def totals(self, year: int) -> Response:
        return Response(**self._request.post(
            "/user/totals",
            token=self.token,
            payload={
                "year": year,
                "user_id": self.user.id
            }))

    def get_limit(self) -> Response:
        return Response(**self._request.get("/user/get-limit", token=self.token))
