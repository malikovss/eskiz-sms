# eskiz-sms
eskiz-sms package for eskiz.uz/sms
# using
```
from eskiz_sms import EskizSMS
email = "your_email@mail.com"
password = "your_password"
eskiz = EskizSMS(email=email, password=password)
eskiz.send_sms('998991234567', 'message', from_whom='4546', callback_url=None)
```
