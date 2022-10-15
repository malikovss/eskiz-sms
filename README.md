# eskiz-sms

eskiz-sms package for eskiz.uz/sms
> :warning: **Please use latest version. In previous versions, there are a lot of mistakes, bugs**
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

if after getting a token, you want to save it somewhere and use until it expires, You can pass token value to the
eskiz_sms instance

```python
from eskiz_sms import EskizSMS

your_saved_token = 'eySomething9320'
eskiz = EskizSMS('email', 'password')
eskiz.token.set(your_saved_token)

eskiz.send_sms('998901234567', message='message')
```

### Saving token to env file

If you set `save_token=True` it will save the token to env file

```python
from eskiz_sms import EskizSMS

eskiz = EskizSMS('email', 'password', save_token=True, env_file_path='.env')
```
