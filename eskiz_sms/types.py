from dataclasses import dataclass
from datetime import datetime
from typing import Union, Optional


@dataclass
class Response:
    id: Optional[str] = None
    status: Optional[str] = None
    data: Optional[Union[dict, list]] = None
    message: Optional[Union[str, dict]] = None


@dataclass
class User:
    id: Optional[int] = None
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    api_token: Optional[str] = None
    status: Optional[str] = None
    sms_api_login: Optional[str] = None
    sms_api_password: Optional[str] = None
    uz_price: Optional[int] = None
    ucell_price: Optional[int] = None
    test_ucell_price: Optional[int] = None
    balance: Optional[int] = None
    is_vip: Optional[bool] = None
    host: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Contact:
    id: Optional[int] = None
    user_id: Optional[int] = None
    group: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    mobile_phone: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class ContactCreated:
    contact_id: int
