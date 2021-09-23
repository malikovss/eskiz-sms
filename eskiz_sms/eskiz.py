from .base import request, Token
from .consts import ApiPaths
from .objects import UserObject, Contact, ContactCreated


class EskizSMS(object):
    def __init__(self, email: str, password: str):
        self.token = Token(email, password)

    def user_data(self):
        data = request.get(ApiPaths.GET_USER, token=self.token)
        return UserObject(**data)

    def add_contact(self, name: str, email: str, group: str, mobile_phone: str):
        data = request.post(ApiPaths.ADD_CONTACT, token=self.token, payload=locals())
        return ContactCreated(**data)

    def update_contact(self, contact_id: int, name: str, group: str, mobile_phone: str):
        data = request.put(ApiPaths.CONTACT.format(id=contact_id), token=self.token, payload=locals())
        return Contact(**data)

    def get_contact(self, contact_id: int):
        data = request.get(ApiPaths.CONTACT.format(id=contact_id), token=self.token)
        return Contact(**data)

    def send_sms(self, mobile_phone: str, message: str, from_whom: str, callback_url: str = None):
        data = request.post(ApiPaths.SEND_SMS, token=self.token, payload=locals())
