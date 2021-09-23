from datetime import datetime

from pydantic import BaseModel


class TokenObject(BaseModel):
    token: str


class ResponseObject(BaseModel):
    message: str = None
    status: str = None
    data: dict = None


class UserObject(BaseModel):
    id: int
    name: str
    email: str
    role: str
    status: str
    sms_api_login: str
    sms_api_password: str
    uz_price: int
    balance: int
    is_vip: bool
    host: str
    created_at: datetime
    updated_at: datetime


class ContactCreated(BaseModel):
    id: int


class Contact(ContactCreated):
    user_id: int
    group: str
    name: str
    email: str
    mobile_phone: str
    created_at: datetime
    updated_at: datetime
