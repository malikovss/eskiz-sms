from typing import Union, Optional, List

from dotenv import get_key, set_key
from pydantic import HttpUrl

from .base import request, Token
from .types import User, Contact, ContactCreated, CallbackUrl, Response

ESKIZ_TOKEN_KEY = "ESKIZ_TOKEN"


class EskizSMS:
    __slots__ = ("token", "__user")

    def __init__(self, email: str, password: str, save_token=False, env_file_path=None):
        self.token = Token(email, password)
        self.__user: Optional[User] = None

        if save_token:
            if env_file_path is None:
                env_file_path = '.env'
            _token = get_key(dotenv_path=env_file_path, key_to_get=ESKIZ_TOKEN_KEY)
            if _token:
                self.token.set(_token)
            else:
                set_key(env_file_path, key_to_set=ESKIZ_TOKEN_KEY, value_to_set=self.token.token)

    @property
    def user(self) -> Optional[User]:
        self.__user = self._user_data()
        return self.__user

    @property
    def _user(self):
        if self.__user is None:
            self.__user = self._user_data()
        return self.__user

    def _user_data(self):
        response = request.get("/auth/user", token=self.token)
        if response.data:
            return User(**response.data)
        return

    def add_contact(self, name: str, email: str, group: str, mobile_phone: str):
        payload = {
            "name": name,
            "email": email,
            "group": group,
            "mobile_phone": str(mobile_phone),
        }
        response = request.post("/contact", token=self.token, payload=payload)
        return ContactCreated(**response.data)

    def update_contact(self, contact_id: int, name: str, group: str, mobile_phone: str):
        payload = {
            "name": name,
            "group": group,
            "mobile_phone": str(mobile_phone),
        }
        data = request.put(f"api/contact/{contact_id}", token=self.token, payload=payload)
        return Contact(**data)

    def get_contact(self, contact_id: int):
        response = request.get(f"api/contact/{contact_id}", token=self.token)
        return Contact(**response.data)

    def send_sms(self, mobile_phone: str, message: str, from_whom: str = '4546',
                 callback_url: Optional[Union[HttpUrl, str]] = None) -> Response:
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
        if callback_url is not None:
            CallbackUrl(url=callback_url)
            payload['callback_url'] = callback_url
        response = request.post("/message/sms/send", token=self.token, payload=payload)
        return response

    def send_global_sms(self, mobile_phone: str, message: str, country_code: str,
                        callback_url: Optional[Union[HttpUrl, str]] = None, unicode: str = "0"):
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
        if callback_url is not None:
            CallbackUrl(url=callback_url)
            payload["callback_url"] = callback_url
        response = request.post("/message/sms/send-global", token=self.token, payload=payload)
        return response

    def send_batch(self, *, messages: List[dict], from_whom: str = "4546", dispatch_id: int) -> Response:
        """
        :param messages: List of messages to send.
            [{"user_sms_id":"sms1","to": 998998046210, "text": "eto test"}]
        :param from_whom: 4546
        :param dispatch_id:
        :returns: Response
        :rtype: eskiz_sms.types.Response
        """
        payload = {
            "messages": [{"user_sms_id": message["user_sms_id"], "to": str(message["to"]), "text": message["text"]} for
                         message in messages],
            "from_whom": from_whom,
            "dispatch_id": dispatch_id
        }
        response = request.post("/message/sms/send-batch", token=self.token, payload=payload)
        return response

    def get_user_messages(self, from_date: str, to_date: str):
        payload = {
            "from_date": from_date,
            "to_date": to_date,
            "user_id": self._user.id
        }
        response = request.get("/message/sms/get-user-messages", token=self.token, payload=payload)
        return response

    def get_user_messages_by_dispatch(self, dispatch_id: int):
        payload = {
            "dispatch_id": dispatch_id,
            "user_id": self._user.id
        }
        response = request.get("/message/sms/get-user-messages-by-dispatch", token=self.token, payload=payload)
        return response

    def get_dispatch_status(self, dispatch_id: int):
        payload = {
            "dispatch_id": dispatch_id,
            "user_id": self._user.id
        }
        response = request.get("/message/sms/get-dispatch-status", token=self.token, payload=payload)
        return response

    def create_template(self, name: str, text: str):
        payload = {
            "name": name,
            "text": text,
        }
        response = request.post("/template", token=self.token, payload=payload)
        return response

    def update_template(self, template_id: int, name: str, text: str):
        payload = {
            "name": name,
            "text": text,
        }
        response = request.put(f"/template/{template_id}", token=self.token, payload=payload)
        return response

    def get_template(self, template_id: int):
        response = request.get(f"/template/{template_id}", token=self.token)
        return response

    def get_templates(self):
        response = request.get("/template", token=self.token)
        return response

    def totals(self, year: int):
        payload = {
            "year": year,
            "user_id": self._user.id
        }
        response = request.post("/user/totals", token=self.token, payload=payload)
        return response

    def get_limit(self):
        response = request.get("/user/get-limit", token=self.token)
        return response
