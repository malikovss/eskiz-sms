# eskiz-sms

eskiz-sms package for eskiz.uz/sms 

[![Downloads](https://static.pepy.tech/personalized-badge/eskiz-sms?period=total&units=international_system&left_color=black&right_color=brightgreen&left_text=Downloads)](https://pepy.tech/project/eskiz-sms)


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
# Don't forget to add env file to .gitignore!
response = eskiz.send_sms('998901234567', message='message')
```
