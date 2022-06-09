from datetime import datetime
from typing import Union

from pydantic import BaseModel, HttpUrl


class CallbackUrl(BaseModel):
    url: HttpUrl = None


class Response(BaseModel):
    status: str = None
    data: dict = None
    message: Union[str, dict] = None


class User(BaseModel):
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
