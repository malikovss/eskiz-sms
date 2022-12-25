import logging
import os

import pytest
from dotenv import load_dotenv

from eskiz_sms import EskizSMS
from eskiz_sms import exceptions, types

load_dotenv()
logging.basicConfig(level=logging.DEBUG)

ESKIZ_INVALID_TOKEN = os.getenv('ESKIZ_INVALID_TOKEN')
ESKIZ_EXPIRED_TOKEN = os.getenv('ESKIZ_EXPIRED_TOKEN')
ESKIZ_TOKEN = os.getenv('ESKIZ_TOKEN')


class TestClass:
    eskiz = EskizSMS(
        email=os.getenv('EMAIL'),
        password=os.getenv('PASSWORD'),
        save_token=False,
        auto_update_token=False
    )

    def test_invalid_token(self):
        self.eskiz.token.set(ESKIZ_INVALID_TOKEN)
        with pytest.raises(exceptions.TokenInvalid):
            self.eskiz.get_limit()

    def test_expired_token(self):
        self.eskiz.token.set(ESKIZ_EXPIRED_TOKEN)
        with pytest.raises(exceptions.TokenInvalid):
            self.eskiz.get_limit()

    def test_valid_token(self):
        self.eskiz.token.set(ESKIZ_TOKEN)
        response = self.eskiz.get_limit()
        assert type(response) == types.Response

    def test_auto_update(self):
        self.eskiz.token.auto_update = True
        self.eskiz.token.set(None)
        response = self.eskiz.get_limit()
        assert type(response) == types.Response

    def test_without_auto_update(self):
        self.eskiz.token.auto_update = False
        self.eskiz.token.set(None)
        response = self.eskiz.get_limit()
        assert type(response) == types.Response

    def test_saving_token(self):
        self.eskiz.token.save_token = True
        self.eskiz.token.set(None)
        self.eskiz.token.env_file_path = '.env'
        response = self.eskiz.get_limit()
        assert type(response) == types.Response
