# eskiz-sms
eskiz-sms package for eskiz.uz/sms
# Installation
```
pip install eskiz_sms
```
# Quickstart
```python
from eskiz_sms import EskizSMS
email = "your_email@mail.com"
password = "your_password"
eskiz = EskizSMS(email=email, password=password)
eskiz.send_sms('998991234567', 'message', from_whom='4546', callback_url=None)
```

### Using pre-saved token
if after getting a token, you want to save it somewhere and use until it expires, You can pass token value to the eskiz_sms instance

```python
from eskiz_sms import EskizSMS

your_saved_token = 'eySomething9320'
eskiz = EskizSMS('email', 'password')
eskiz.token.token = your_saved_token

eskiz.send_sms('998901234567', message='message')
```