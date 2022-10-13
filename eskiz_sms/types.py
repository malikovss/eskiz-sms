from datetime import datetime
from typing import Union, Optional

from pydantic import BaseModel, HttpUrl


class CallbackUrl(BaseModel):
    url: HttpUrl = None


class Response(BaseModel):
    status: str = None
    data: dict = None
    message: Union[str, dict] = None
    status_code: int = None


class User(BaseModel):
    id: Optional[int]
    name: Optional[str]
    email: Optional[str]
    role: Optional[str]
    status: Optional[str]
    sms_api_login: Optional[str]
    sms_api_password: Optional[str]
    uz_price: Optional[int]
    balance: Optional[int]
    is_vip: Optional[bool]
    host: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class ContactCreated(BaseModel):
    contact_id: int


class Contact(ContactCreated):
    user_id: int
    group: str
    name: str
    email: str
    mobile_phone: str
    created_at: datetime
    updated_at: datetime
