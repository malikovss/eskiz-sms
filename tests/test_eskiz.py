import os

from eskiz_sms import EskizSMS
from dotenv import load_dotenv

load_dotenv()


eskiz = EskizSMS(
    email=os.getenv('EMAIL'),
    password=os.getenv('PASSWORD'),
    save_token=True,
    is_async=True
)

response = eskiz.get_limit()

print(response)
