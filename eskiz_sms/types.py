from datetime import datetime
from typing import Union, Optional

from pydantic import BaseModel, HttpUrl


class CallbackUrl(BaseModel):
    url: HttpUrl


class Response(BaseModel):
    id: Optional[str]
    status: Optional[str]
    data: Optional[dict]
    message: Optional[Union[str, dict]]


class User(BaseModel):
    id: Optional[int]
    name: Optional[str]
    email: Optional[str]
    role: Optional[str]
    api_token: Optional[str]
    status: Optional[str]
    sms_api_login: Optional[str]
    sms_api_password: Optional[str]
    uz_price: Optional[int]
    ucell_price: Optional[int]
    balance: Optional[int]
    is_vip: Optional[bool]
    host: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class ContactCreated(BaseModel):
    contact_id: int


class Contact(ContactCreated):
    id: Optional[int]
    user_id: Optional[int]
    group: Optional[str]
    name: Optional[str]
    email: Optional[str]
    mobile_phone: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
