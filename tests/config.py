import os

from dotenv import load_dotenv

from eskiz_sms import EskizSMS
from eskiz_sms.async_ import EskizSMS as EskizSMSAsync

load_dotenv()

EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')
ESKIZ_INVALID_TOKEN = os.getenv('ESKIZ_INVALID_TOKEN')
ESKIZ_EXPIRED_TOKEN = os.getenv('ESKIZ_EXPIRED_TOKEN')
ESKIZ_TOKEN = os.getenv('ESKIZ_TOKEN')


def get_eskiz_instance(save_token=True, auto_update_token=True):
    return EskizSMS(
        email=EMAIL,
        password=PASSWORD,
        save_token=save_token,
        auto_update_token=auto_update_token
    )


def get_eskiz_async_instance(save_token=True, auto_update_token=True):
    return EskizSMSAsync(
        email=EMAIL,
        password=PASSWORD,
        save_token=save_token,
        auto_update_token=auto_update_token
    )
