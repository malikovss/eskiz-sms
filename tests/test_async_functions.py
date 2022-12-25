import pytest

from eskiz_sms.async_ import EskizSMS
from tests import config


@pytest.fixture
def eskiz():
    return config.get_eskiz_async_instance()


class TestAsyncFunctions:
    async def test_property_user(self, eskiz: EskizSMS):
        user = await eskiz.user
        assert user.email == config.EMAIL
