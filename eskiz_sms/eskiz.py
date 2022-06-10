from typing import Union, Optional, List

from pydantic import HttpUrl

from .base import request, Token
from .types import User, Contact, ContactCreated, CallbackUrl


class EskizSMS(object):
    def __init__(self, email: str, password: str):
        self.token = Token(email, password)
        self.__user: Optional[User] = None

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
        response = request.post("/contact", token=self.token, payload=locals())
        return ContactCreated(**response.data)

    def update_contact(self, contact_id: int, name: str, group: str, mobile_phone: str):
        data = request.put(f"api/contact/{contact_id}", token=self.token, payload=locals())
        return Contact(**data)

    def get_contact(self, contact_id: int):
        response = request.get(f"api/contact/{contact_id}", token=self.token)
        return Contact(**response.data)

    def send_sms(self, mobile_phone: str, message: str, from_whom: str = '4546',
                 callback_url: Optional[Union[HttpUrl, str]] = None):
        if callback_url is not None:
            CallbackUrl(url=callback_url)
        response = request.post("/message/sms/send", token=self.token, payload=locals())
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
        if callback_url is not None:
            CallbackUrl(url=callback_url)
        response = request.post("/message/sms/send-global", token=self.token, payload=locals())
        return response

    def send_batch(self, *, messages: List[dict], from_whom: str = "4546", dispatch_id: int):
        """
        :param messages: List of messages to send.
            [{"user_sms_id":"sms1","to": 998998046210, "text": "eto test"}]
        :param from_whom: 4546
        :param dispatch_id:
        :return:
        """
        response = request.post("/message/sms/send-batch", token=self.token, payload=locals())
        return response

    def get_user_messages(self, from_date: str, to_date: str):
        _payload = locals()
        _payload["user_id"] = self._user.id
        response = request.get("/message/sms/get-user-messages", token=self.token, payload=_payload)
        return response

    def get_user_messages_by_dispatch(self, dispatch_id: int):
        _payload = locals()
        _payload["user_id"] = self._user.id
        response = request.get("/message/sms/get-user-messages-by-dispatch", token=self.token, payload=_payload)
        return response

    def get_dispatch_status(self, dispatch_id: int):
        _payload = locals()
        _payload["user_id"] = self._user.id
        response = request.get("/message/sms/get-dispatch-status", token=self.token, payload=_payload)
        return response

    def create_template(self, name: str, text: str):
        response = request.post("/template", token=self.token, payload=locals())
        return response

    def update_template(self, template_id: int, name: str, text: str):
        response = request.put(f"/template/{template_id}", token=self.token, payload=locals())
        return response

    def get_template(self, template_id: int):
        response = request.get(f"/template/{template_id}", token=self.token)
        return response

    def get_templates(self):
        response = request.get("/template", token=self.token)
        return response

    def totals(self, year: int):
        _payload = locals()
        _payload["user_id"] = self._user.id
        response = request.post("/user/totals", token=self.token, payload=_payload)
        return response

    def get_limit(self):
        response = request.get("/user/get-limit", token=self.token)
        return response
